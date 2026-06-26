import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

def test_smtp_connection(host, port, sender, password) -> dict:
    """Verifies connection and credentials with the SMTP server."""
    try:
        port = int(port)
        if port == 465:
            # SSL Connection
            server = smtplib.SMTP_SSL(host, port, timeout=5)
        else:
            # TLS Connection (port 587 or 25)
            server = smtplib.SMTP(host, port, timeout=5)
            server.starttls()
            
        if sender and password:
            server.login(sender, password)
            
        server.quit()
        return {"success": True, "message": "SMTP connection and authentication successful!"}
    except Exception as e:
        logger.error(f"SMTP diagnostic failed: {str(e)}")
        return {"success": False, "error": str(e)}

def send_html_email(host, port, sender, password, recipient, subject, body_html) -> dict:
    """Sends a beautifully formatted HTML email via smtplib."""
    try:
        port = int(port)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        
        # Attach HTML body
        msg.attach(MIMEText(body_html, "html"))
        
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            
        if sender and password:
            server.login(sender, password)
            
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient} with subject: '{subject}'")
        return {"success": True, "message": f"Email successfully sent to {recipient}."}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"success": False, "error": str(e)}

def build_job_alert_email_template(candidate_name, jobs) -> str:
    """Generates an HTML email for job matches."""
    job_items_html = ""
    for j in jobs:
        score_color = "#10b981" if j.get('match_score', 0) >= 85 else "#06b6d4" if j.get('match_score', 0) >= 70 else "#f59e0b"
        job_items_html += f"""
        <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
            <h3 style="margin: 0; color: #1e293b;">{j.get('title')} <span style="font-size: 14px; font-weight: bold; color: {score_color}; margin-left: 10px;">{j.get('match_score')}% Match</span></h3>
            <p style="margin: 5px 0; font-weight: 600; color: #475569;">{j.get('company')} — {j.get('location')}</p>
            <p style="margin: 5px 0; color: #64748b; font-size: 14px;"><strong>Missing Skills:</strong> {', '.join(j.get('missing_skills', [])) or 'None'}</p>
            <p style="margin: 10px 0 0 0;"><a href="{j.get('url')}" style="color: #8b5cf6; text-decoration: none; font-weight: bold; font-size: 14px;">View Job Posting &rarr;</a></p>
        </div>
        """
        
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; margin: 0; color: #334155;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); padding: 30px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px;">New Job Matches Found!</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Career Twin Agent Alerts</p>
            </div>
            <div style="padding: 25px;">
                <p style="font-size: 16px;">Hello <strong>{candidate_name}</strong>,</p>
                <p style="font-size: 14px; line-height: 1.5;">Our Career Twin Agent has completed a sweep of the job market and identified the following matches based on your updated profile:</p>
                
                <div style="margin: 20px 0; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
                    {job_items_html}
                </div>
                
                <p style="font-size: 14px; line-height: 1.5;">To review or apply for these opportunities, log into your Streamlit portal and access the Job Discovery workspace.</p>
            </div>
            <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0;">&copy; 2026 TalentAI Career Twin Agent. All rights reserved.</p>
                <p style="margin: 5px 0 0 0;">This is an automated notification. To configure alerts, visit settings in the application.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def build_application_summary_email_template(candidate_name, logs) -> str:
    """Generates an HTML email summarizing applied jobs."""
    log_items_html = ""
    for log in logs:
        status_color = "#10b981" if log.get('status') == 'applied' else "#f43f5e" if log.get('status') == 'failed' else "#f59e0b"
        log_items_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-size: 14px; color: #1e293b;"><strong>{log.get('company')}</strong><br><span style="font-size: 12px; color: #64748b;">{log.get('title')}</span></td>
            <td style="padding: 12px; font-size: 14px; color: #475569;">{log.get('applied_at', '').split('T')[0]}</td>
            <td style="padding: 12px; font-size: 14px; font-weight: bold; color: {status_color}; text-transform: uppercase;">{log.get('status')}</td>
        </tr>
        """
        
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; margin: 0; color: #334155;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #f43f5e 100%); padding: 30px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px;">Application Activity Report</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Career Twin Agent Tracker</p>
            </div>
            <div style="padding: 25px;">
                <p style="font-size: 16px;">Hello <strong>{candidate_name}</strong>,</p>
                <p style="font-size: 14px; line-height: 1.5;">Here is the latest job application activity summary generated by your autonomous Application Agent:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; text-align: left;">
                    <thead>
                        <tr style="background-color: #f1f5f9; border-bottom: 2px solid #e2e8f0;">
                            <th style="padding: 12px; font-size: 14px; color: #475569; font-weight: bold;">Company & Position</th>
                            <th style="padding: 12px; font-size: 14px; color: #475569; font-weight: bold;">Date</th>
                            <th style="padding: 12px; font-size: 14px; color: #475569; font-weight: bold;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {log_items_html}
                    </tbody>
                </table>
                
                <p style="font-size: 14px; line-height: 1.5;">To review detail logs, take action on pending applications, or run recruiter mock interviews, visit the portal dashboard.</p>
            </div>
            <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0;">&copy; 2026 TalentAI Career Twin Agent. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
