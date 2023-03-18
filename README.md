# mbox-to-md
Intelligently converts mbox to Markdown

This Python 3 script takes an mbox file as input and attempts to deconstruct it as Markdown friendly text files. Some features are

- Names the Markdown files based on the date the message was sent, the sender and the subject
- Organizes the Markdown files based on the Sender name
- Includes attachments. Checks to see if the attachment is already there and incriments if needed
- Adds a Markdown style link to the bottom of the message to the attachment, if it exists.
- Writes an errors.txt log with processing errors

To Do list--

- Comment the code better
- Don't create an Attachments folder if there is no attachment
- Use a checksum to test to see if an attachment with the same filename and checksome match exists in the sender's Attachments folder. If so, just create alink to the old one and get on with life...
- Create code blocks to surround html content so it looks better in Obsidian...