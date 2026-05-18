package com.bhargav.automation.utils;

import java.io.File;
import java.util.Properties;

import jakarta.mail.Authenticator;
import jakarta.mail.Message;
import jakarta.mail.PasswordAuthentication;
import jakarta.mail.Session;
import jakarta.mail.Transport;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeBodyPart;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;

public class EmailUtils {

	public static void sendTestReport(String reportPath) {
		final String senderEmail = "bhargav.automation@gmail.com";
		final String appPassword = "your_app_password_here";
		final String recipientEmail = "bhargav.automation@gmail.com";

		Properties prop = new Properties();
		prop.put("mail.smtp.auth", "true");
		prop.put("mail.smtp.host", "smtp.gmail.com");
		prop.put("mail.smtp.starttls.enable", "true");
		prop.put("mail.smtp.port", "587");

		Session session = Session.getInstance(prop, new Authenticator() {
			protected PasswordAuthentication getPasswordAuthentication() {
				return new PasswordAuthentication(senderEmail, appPassword);
			}
		});
		session.setDebug(true);

		try {
			Message message = new MimeMessage(session);
			message.setFrom(new InternetAddress(senderEmail));
			message.setRecipients(Message.RecipientType.TO, InternetAddress.parse(recipientEmail));
			message.setSubject("Test Email From Bhargav's Automation Framework");

			MimeBodyPart textPart = new MimeBodyPart();
			textPart.setText("Hello \n\n This is a test email from Bhargav's Automation Framework \n\n Regards,\nBhargav");

			MimeBodyPart attachmentPart = new MimeBodyPart();
			System.out.println("Attachment path is - " + reportPath);
			attachmentPart.attachFile(new File(reportPath));

			MimeMultipart multipart = new MimeMultipart();
			multipart.addBodyPart(textPart);
			multipart.addBodyPart(attachmentPart);
			message.setContent(multipart);

			Transport.send(message);
			System.out.println("Email Sent Successfully ***");

		} catch (Exception e) {
			e.printStackTrace();
		}

	}

}