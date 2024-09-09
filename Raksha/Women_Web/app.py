from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_mail import Mail, Message
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import cv2

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['UPLOAD_FOLDER'] = './static'  # Directory to store recorded video

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dutsujan07@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'iqmc rnrz ptcx srvx'   # Replace with your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Function to capture live video and detect person
def capture_video_and_detect_person(video_filename, duration=10):
    cap = cv2.VideoCapture(0)  # Use '0' for the default webcam
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # Codec
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (640, 480))

    frame_count = 0
    fps = 20  # Assuming 20 frames per second
    max_frames = duration * fps  # Duration in seconds

    # Load pre-trained person detection model (Haar Cascade for example)
    person_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

    while frame_count < max_frames:
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            bodies = person_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Draw rectangle around detected person
            for (x, y, w, h) in bodies:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            out.write(frame)  # Write frame to file
        else:
            break
        frame_count += 1

    cap.release()
    out.release()
    print(f"Video successfully saved to {video_filename}")

# Function to send an email with video or SOS
def send_email(sender_email, sender_password, recipient_email, subject, body, video_path=None):
    msg = MIMEMultipart() if video_path else Message(subject)
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if video_path:
        try:
            with open(video_path, 'rb') as video_file:
                part = MIMEApplication(video_file.read(), Name=os.path.basename(video_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(video_path)}"'
                msg.attach(part)
        except FileNotFoundError:
            print(f"Error: The file {video_path} was not found.")
            return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient_email}.")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

# Serve the frontend HTML page
@app.route('/')
def index():
    return render_template('index.html')  # This will render 'index.html' from 'templates' folder

# Route to serve sujan.html
@app.route('/sujan')
def sujan():
    return render_template('sujan.html')

# Endpoint to receive location and voice data
@app.route('/send-sos', methods=['POST'])
def send_sos():
    try:
        # Get location data
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        # Get voice file
        voice_file = request.files['voice']

        # Save the voice file temporarily
        voice_path = os.path.join('uploads', voice_file.filename)
        voice_file.save(voice_path)

        # Compose the email
        msg = Message('SOS Alert - Immediate Help Needed',
                      sender='dutsujan07@gmail.com',
                      recipients=['sujandut07@gmail.com'])  # Recipient's email
        msg.body = f"https://www.google.com/maps?q={latitude},{longitude}"

        # Attach the voice file
        with app.open_resource(voice_path) as fp:
            msg.attach(voice_file.filename, 'audio/ogg', fp.read())

        # Send email
        mail.send(msg)

        # Clean up and remove the temporary file
        os.remove(voice_path)

        return jsonify({'message': 'SOS email sent successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'message': 'Failed to send SOS email'}), 500

# Route for handling the video recording and email sending
@app.route('/send_video', methods=['POST'])
def send_video():
    if 'video' not in request.files:
        return jsonify({'message': 'No video file provided.'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400

    video_filename = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
    video_file.save(video_filename)

    # Send the email with the predefined details
    send_email(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], 'sujandut07@gmail.com', 'Subject: Live Video File', 'Please find the attached live video file.', video_filename)
    flash('Video captured and email sent successfully!')
    
    return jsonify({'message': 'Video file uploaded and email sent successfully.'})

if __name__ == '__main__':
    # Ensure the upload directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True, port=5000)
