import os
from flask import Flask, redirect, url_for, flash
import cv2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['UPLOAD_FOLDER'] = './static'  # Directory to store recorded video

# Predefined email details
SENDER_EMAIL = "dutsujan07@gmail.com"
SENDER_PASSWORD = "czuv fdmt howo pmml"  # App-specific password recommended
RECIPIENT_EMAIL = "dasvivek398@gmail.com"
EMAIL_SUBJECT = "Subject: Live Video File"
EMAIL_BODY = "Please find the attached live video file."

# Function to capture live video
def capture_video(video_filename, duration=10):
    cap = cv2.VideoCapture(0)  # Use '0' for the default webcam
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # Codec
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (640, 480))

    frame_count = 0
    fps = 20  # Assuming 20 frames per second
    max_frames = duration * fps  # Duration in seconds

    while frame_count < max_frames:
        ret, frame = cap.read()
        if ret:
            out.write(frame)  # Write frame to file
        else:
            break
        frame_count += 1

    cap.release()
    out.release()
    print(f"Video successfully saved to {video_filename}")

# Function to send the recorded video via email
def send_email(sender_email, sender_password, recipient_email, subject, body, video_path):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

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

# Route for handling the video recording and email sending
@app.route('/send_video')
def send_video():
    # Capture video
    video_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'live_video.avi')
    capture_video(video_filename)

    # Send the email with the predefined details
    send_email(SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, EMAIL_SUBJECT, EMAIL_BODY, video_filename)
    flash('Video captured and email sent successfully!')
    
    return redirect(url_for('index'))

# Route for the home page (basic landing page)
@app.route('/')
def index():
    return "<h1>Welcome! To capture and send the video, visit <a href='/send_video'>this link</a>.</h1>"

if __name__ == '__main__':
    app.run(debug=True)
