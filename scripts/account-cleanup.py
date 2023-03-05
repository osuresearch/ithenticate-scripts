# v0.0.2
#
# This script will use the iThenticate API (https://help.turnitin.com/ithenticate/ithenticate-developer/api/api-guide.htm)
# to first log in and obtain a session ID.  Using the session ID, loop through a list of
# user IDs and call the API to drop the user.
#
# Note: The iThenticate API as a 60 request/second, per user limit.

import requests
import getpass
import re
import xml.etree.ElementTree as et
import json
import argparse
import time
import tkinter
from tkinter.filedialog import askopenfilename
from datetime import datetime


class Error:
    def __init__(self, status, name, message):
        self.status = status
        self.name = name
        self.message = message


def callApi(data, printResponseContent = False):
    url = 'https://api.ithenticate.com/rpc'
    headers = { 'Content-Type': 'application/xml' }

    # Give the server time to recuperate from our bombardment.
    tryLimit = 10
    response = ''
    while response == '' and tryLimit > 0:
        tryLimit -= 1
        try:
            response = requests.post(url, headers=headers, data=data.strip())
            break
        except:
            if tryLimit <= 0:
                # Stop trying
                print()
                print("Server kept refusing connection.")
                print()
                exit()
            print()
            print("++++++++++++++++++++++++++++Connection refused by server. Resting ...", end='', flush=True)
            time.sleep(3)
            print("Done")
            print()
            continue
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/xml; charset=UTF-8'

    # Debugging
    if printResponseContent:
        print()
        print(response.content)
        print()

    # https://docs.python.org/3/library/xml.etree.elementtree.html?highlight=etree
    tree = et.fromstring(response.content)

    # Get the api_status
    member = tree.find("./params/param/value/struct/member[name='api_status']")
    api_status = int(member.find('value/int').text)

    # Check for errors
    if api_status != 200:
        # Check for invalid username
        member = tree.find("./params/param/value/struct/member[name='errors']")
        if member is not None:
            error_name = member.find('value/struct/member/name').text
            error_message = member.find('value/struct/member/value/array/data/value/string').text
            return False, Error(api_status, error_name, error_message)
        
        # Check for invalid login
        member = tree.find("./params/param/value/struct/member[name='messages']")
        if member is not None:
            error_name = 'login'
            error_message = member.find('value/array/data/value/string').text
            return False, Error(api_status, error_name, error_message)

    return True, tree


def getSid(username, password):
    success, response = callApi(f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <methodCall>
            <methodName>login</methodName>
            <params>
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>username</name>
                                <value>
                                    <string>{username}</string>
                                </value>
                            </member>
                            <member>
                                <name>password</name>
                                <value>
                                    <string>{password}</string>
                                </value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        </methodCall>
    """)

    if not success:
        print(f"ERROR: ({response.status}) {response.name} -> {response.message}")
        exit()

    # Store the session ID
    member = response.find("./params/param/value/struct/member[name='sid']")
    if member is None:
        print(f"ERROR: Session ID not found!")
        exit()

    return member.find('value/string').text


def dropUser(sid, userId):
    success, response = callApi(f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <methodCall>
            <methodName>user.drop</methodName>
            <params>
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>sid</name>
                                <value><string>{sid}</string></value>
                            </member>
                            <member>
                                <name>id</name>
                                <value><int>{userId}</int></value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        </methodCall>
    """)

    if not success:
        return f"ERROR: ({response.status}) {response.name} -> {response.message}"

    else:
        member = response.find("./params/param/value/struct/member[name='messages']")
        if member is not None:
            message = member.find("value/array/data/value/string").text
            return f"{message}!"


# Get command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("-u", "--username", help="the API username", type=str)
argParser.add_argument("-p", "--password", help="the API password", type=str)
argParser.add_argument("-r", "--renewSid", help="number of seconds before renewing the API Session ID; defaults to 20", type=int, default=20)
argParser.add_argument("-f", "--jsonFile", help="the JSON file listing user data to process", type=str)
argParser.add_argument("-d", "--days", help="user records that have not logged in for this number of days or more will be removed; defaults to 1,095 days (3 years)", type=int, default=1095)
argParser.add_argument("-n", "--numberToProcess", help="specify the number of users to process", type=int)
argParser.add_argument("-b", "--numberToProcessBeforePausing", help="batch size; specify the number of users to process before pausing to avoid the API request limit; defaults to 40", type=int, default=40)
argParser.add_argument("-s", "--secPause", help="the number of seconds to pause between batches; defaults to 1", type=int, default=1)
argParser.add_argument("-o", "--offset", help="the number of user records to ignore at the beginning", type=int, default=0)
argParser.add_argument("-v", "--verbosity", help="verbosity; print out the records skipped when offset is specified", action="store_true")
argParser.add_argument("-t", "--testOnly", help="test run showing what would have been processed, but the Drop API is not called", action="store_true")
args = argParser.parse_args()

username = args.username
password = args.password
renewSid = 20 if args.renewSid < 0 else args.renewSid
jsonFile = args.jsonFile
days = 1095 if args.days < 0 else args.days
numberToProcess = 0 if args.numberToProcess < 0 else args.numberToProcess
numberToProcessBeforePausing = 40 if args.numberToProcessBeforePausing < 0 else args.numberToProcessBeforePausing
secPause = 1 if args.secPause < 0 else args.secPause
offset = 0 if args.offset < 0 else args.offset
verbosity = args.verbosity
testOnly = args.testOnly


# Start the script
print()
print ('iThenticate Account Cleanup')
print ('=============================')
print()

print(f"Days last login check: {days}")
print(f"Number per batch before pausing: {numberToProcessBeforePausing}")
print(f"Number to process in total: {numberToProcess or 'All'}")
print(f"User list offset: {offset or 'None'}")
print(f"Show offsets: {'Yes' if verbosity else 'No'}")
print(f"Test only: {'Yes' if testOnly else 'No'}")
print()

if username is None:
    username = input('Enter the API username: ')

if password is None:
    password = getpass.getpass('Enter the API password: ')

sid = getSid(username, password)
print(f"SID: {sid}")


# Continue on if we are able to get a valid session ID

# Specify the JSON file containing the list of user data
tk = tkinter.Tk()
if jsonFile is None:
    jsonFile = askopenfilename(filetypes=[("JSON File", ".json")], title="Choose the JSON file listing user data.")

# Open JSON file
if jsonFile is None or jsonFile == '':
    print(f"ERROR: No JSON file specified!")
    exit()

print(f"File: {jsonFile}")
fh = open(jsonFile)
tk.destroy() # close the tkinter instance
print()

# JSON to dictionary
print(f"Check for user logins >/= {days} days")
print("---------------------------------------")
print()

index = 0
limitCount = 0
pauseCount = 0
limit = numberToProcess
checkTime = 0
data = json.load(fh)
for user in data:
    index += 1

    # Check if we need to renew the session ID
    if checkTime == 0 or time.monotonic() - checkTime > renewSid:
        sid = getSid(username, password)
        print(f"RENEWED SID: {sid}")
        print()
        checkTime = time.monotonic()

    # Check for offset
    if offset is not None and index <= offset:
        if verbosity:
            print(f"{index}) SKIPPING User: ({user['id']}) {user['email']}")
        continue
    elif offset is not None and index == offset + 1:
        if verbosity:
            print()

    # Check for limit
    limitCount += 1
    if limit is not None and limitCount > limit:
        break

    # user = {
    #     'is_admin': 0,
    #     'report_group': None,
    #     'email': 'saidi.3@osu.edu',
    #     'setup_time': '2017-05-19 21:47:04',
    #     'first_name': 'Nassima',
    #     'last_login_time': '2023-02-04 15:31:14',
    #     'is_disabled': 0,
    #     'last_name': 'Saidi',
    #     'time_zone': 'America/New_York',
    #     'id': 386385
    # }
    lastLogin = datetime.strptime(user['last_login_time'], '%Y-%m-%d %H:%M:%S')
    diff = datetime.now() - lastLogin

    print(f"{index}) User: ({user['id']}) {user['email']}")
    print(f"Last login: {user['last_login_time']}") # '2023-02-04 15:31:14'
    print(f"{diff.days} days since last login")

    if diff.days >= days:
        # Record needs to be dropped
        if testOnly:
            print("** WILL BE DROPPED **")
        else:
            # Drop user record
            print(f"DROPPING {id} ... ", end='', flush=True)
            msg = dropUser(sid, user['id'])
            print("Done")
            print(f"    {msg}")

            # Check if pausing API calls
            pauseCount += 1
            if pauseCount > numberToProcessBeforePausing:
                print()
                print("Pausing ... ", end='', flush=True)
                time.sleep(secPause)
                pauseCount = 0
                print("Done")
    else:
        print("RETAIN")
    
    print()


# Exit
print()
