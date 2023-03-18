# Import necessary libraries
import os
import re
from pathlib import Path
import mailbox
from email.utils import parseaddr
from email import policy
import base64
import email.utils
import datetime


# Define a function to sanitize filenames
def sanitize_filename(filename, max_length=250):
    # Check if the filename is a valid string
    if not isinstance(filename, str):
        log_error('Invalid filename', filename)
        return 'unknown_subject'

    # Check if the subject is not available or is invalid
    if filename.startswith('=?'):
        log_error('Invalid subject', filename)
        return 'Unknown Subject'

    # Only include letters, numbers, spaces, underscores, and hyphens
    legal_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-')
    filename = ''.join(c for c in filename if c in legal_chars)

    # Truncate the filename if it's too long
    if len(filename) > max_length:
        log_error("Filename too long", f"filename: {filename}")
        filename = filename[:max_length]
    return filename

# Define a function to get the sender's name
def get_sender_name(msg):
    # Get the sender's email address
    sender = msg['From']
    if not sender:
        return "Unknown"

    try:
        # Parse the sender's name and email address
        name, addr = email.utils.parseaddr(str(sender))
        if name:
            return name
        return addr
    except TypeError as e:
        log_error("Error parsing sender name", f"sender: {sender}, error: {str(e)}")
        return "Error_parsing_sender"

# Define a function to truncate filenames
def truncate_filename(filename, max_length):
    basename, ext = os.path.splitext(filename)
    if len(basename) > max_length:
        basename = basename[:max_length - len(ext) - 3] + '...'
        return basename + ext
    else:
        return filename

# Define a function to log errors
def log_error(message, details):
    with open(os.path.join(source_dir, 'errors.txt'), 'a') as f:
        f.write(f"{message}: {details}\n")

# Define a function to decode email payloads
def decode_payload(part):
    charset = part.get_content_charset() or 'utf-8'

    charset_match = re.search(r'([\w-]+)', charset)
    if charset_match:
        charset = charset_match.group(1)

    payload = part.get_payload(decode=True)

    # Try to decode the payload using different charsets
    try:
        return payload.decode(charset)
    except LookupError:
        log_error('Unknown encoding', charset)
    except UnicodeDecodeError:
        pass

    try:
        return payload.decode('utf-8')
    except UnicodeDecodeError:
        pass

    try:
        return payload.decode('ISO-8859-1')
    except UnicodeDecodeError:
        pass

    log_error('Failed to decode payload', f'charset: {charset}')
    return ''

# Define a function to extract email attachments
def extract_attachments(msg, output_dir):
    attachment_links = []
    attachments_dir = os.path.join(output_dir, "Attachments")
    os.makedirs(attachments_dir, exist_ok=True)

    # Iterate through email parts to find attachments
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        file_path = os.path.join(attachments_dir, filename)

        # Ensure that the file does not already exist
        counter = 1
        while os.path.isfile(file_path):
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(attachments_dir, new_filename)
            counter += 1

        # Check if the payload is not None before writing the attachment
        payload = part.get_payload(decode=True)
        if payload:
            with open(file_path, "wb") as f:
                f.write(payload)
        else:
            log_error("Attachment payload is None", f"filename: {filename}")

        attachment_links.append(f"[{filename}]({file_path})")

    return attachment_links

# Define a function to process each email
def process_email(msg, source_dir):
    try:
        # Get the email headers
        sender = msg['From']
        to = msg['To']
        cc = msg['Cc']
        subject = msg['Subject']

        # Get the formatted date
        sent_date = msg['Date']
        parsed_date = email.utils.parsedate_to_datetime(sent_date)
        if parsed_date:
            formatted_date = parsed_date.strftime('%Y-%m-%d %H-%M-%S')
        else:
            formatted_date = "unknown_date"
            log_error("Failed to parse date", sent_date)

        # Create the output file name and path
        sender_name = get_sender_name(msg)
        sanitized_subject = sanitize_filename(subject)
        output_file_name = f"({formatted_date}) {sender_name} -- {sanitized_subject}.md"
        output_dir = os.path.join(source_dir, sender_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, output_file_name)

        # Write the email headers to the output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # Write the simplified  markdown header block to the output file
            # Open and close a Markdown code block
            f.write("```markdown\n")
            f.write(f"**From:** {sender}\n")
            f.write(f"**To:** {to}\n")
            f.write(f"**CC:** {cc}\n")
            f.write(f"**Subject:** {subject}\n")
            f.write("```\n\n")
            f.write("---\n\n")

            # Write the email body to the output file
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        f.write(decode_payload(part))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    f.write(decode_payload(msg))

            # Write the attachment links to the output file
            attachment_links = extract_attachments(msg, output_dir)
            if attachment_links:
                f.write("\n\nAttachments:\n")
                for link in attachment_links:
                    f.write(f"{link}\n")

        print(f"Converted: {output_file_path}")
    except Exception as e:
        log_error("Failed to process email", str(e))
        
# Define a function to process mbox mailboxes
def process_mbox(source_file, source_dir):
    mbox = mailbox.mbox(source_file, create=False)
    mbox.lock()

    try:
        # Iterate through all the emails in the mailbox and process each one
        for msg in mbox:
            process_email(msg, source_dir)
    finally:
        mbox.unlock()

# Set the source file and source directory
source_file = '/Users/path/to/your.mbox'
source_dir = os.path.dirname(source_file)

# Call the process_mbox function to start the mbox to markdown conversion
process_mbox(source_file, source_dir)