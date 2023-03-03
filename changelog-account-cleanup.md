# Change Log - Account Cleanup

## 0.0.2

- Add in "-u", "--username" command line argument
- Add in "-p", "--password" command line argument
- Add in "-f", "--jsonFile" command line argument
- Add in "-r", "--renewSid" command line argument
- Add in "-s", "--secPause" command line argument
- Add in "-t", "--testOnly" command line argument
- Add in "-d", "--days" command line argument
- Changed command line argument "-p", for the number to process before pausing, into "-b" for "batch", and assigned "-p" to "password" instead
- Removed "-q", "--quiet" command line argument
- Avoid API request failures due to the server refusing the connection by retrying every 3 seconds
- Display the record number as they are organized in the JSON file
- Organize code and output display
- Change command line argument "-so" to "-v" for "verbosity"

## 0.0.1

- Initial deployment