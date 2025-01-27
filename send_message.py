import pywhatkit as kit

phone_number = "+254731315770"  # Include country code
message = "No you don't!"

# Schedule the message
kit.sendwhatmsg(phone_number, message, 16, 10, 15, True, 2)
