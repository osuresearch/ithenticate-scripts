# iThenticate Scripts

A collection of scripts for the iThenticate app.  The list of scripts are as follows:


## Account Cleanup Script

File: `account-cleanup.py`  
Language: [Python 3](https://docs.python.org/3/library/index.html)  
Description: Using the list of users from iThenticate, flag all who have not logged in to the site in the last 3 years.  List those records and ask for confirmation to proceed and call the Drop API on those users.

### Requirement

- [Python 3](https://docs.python.org/3/library/index.html)
    - Install the `Requests` module for Python 3: https://www.geeksforgeeks.org/how-to-install-requests-in-python-for-windows-linux-mac/
    - In Mac, you can try running `python3 -m pip install requests` if the above does not work
- iThenticate Admin credentials
- iThenticate API credentials (https://pam.osu.edu/SecretServer/app/#/secret/53266/general)

### Usage

1. Log into the iThenticate Admin UI: https://go.osu.edu/ithenticate
2. Go to `Manage Users`
3. Download the users in `json` format (the site provides xls, csv, or json)
4. Run `python account-cleanup.py`
    - Some Python installation use `python`, `python3`, `py`, and/or `py3`
    - Command line arguments:

        |Argument|Expected Value|Description|
        |--------|--------------|-----------|
        |-u|string|the API username; if not specified, then the user will be prompt to enter it|
        |-p|string|the API password; if not specfied, then the user will be prompt to enter it|
        |-r|integer|(Default: 20) number of seconds before renewing the API Session ID|
        |-f|string|the JSON file listing user data to process; if not specified, then the user will be prompt to select it|
        |-d|integer|(Default: 1095) user records that have not logged in for this number of days or more will be removed|
        |-n|integer|(Default: all) limit the number of users to process|
        |-b|integer|(Default: 40) batch size; specify the number of users to process before pausing to avoid the API request limit|
        |-s|integer|(Default: 1) the number of seconds to pause between batches|
        |-o|integer|(Default: no offset) the number of user records to ignore at the beginning|
        |-v|n/a|verbosity; print out the records skipped when offset is specified|
        |-t|n/a|test run showing what would have been processed, but the Drop API is not called|

    - Examples:

        Note: Only records flagged (last login greater than 3 years ago) to be processed are counted.

        `python account-cleanup.py` : process all user records in the JSON file, pausing every 40  
        `python account-cleanup.py -u myusername -p mypassword -j ~/download/users.json` : process all user records in the JSON file, pausing every 40, skipping the login and file selection prompts  
        `python account-cleanup.py -n 50 -b 20` : process the first 50 user records, pausing every 20  
        `python account-cleanup.py -n 100 -b 20 -s 3 -o 50` : process 100 user records after skipping the first 50, pausing every 20 for 3 seconds  
        `python account-cleanup.py -n 100 -b 20 -o 50 -v` : process 100 user records after skipping the first 50, pausing every 20, printing out the records skipped  
        `python account-cleanup.py -n 50 -t` : process 50 user records, but only as a test-run  

    - The script will ask for an iThenticate API credential to login (unless the `u` and/or `p` arguments are specified).
    - The script will ask to select the JSON file downloaded from iThenticate (unless the `j` argument is specified).
    - To only do a test-run, and not actually call the Drop API, use the `t` argument.

### Reference: API Response Format

Invalid username

```xml
<?xml version="1.0" encoding="utf-8"?>
<methodResponse>
    <params>
        <param>
            <value>
                <struct>
                    <member>
                        <name>status</name>
                        <value>
                            <int>500</int>
                        </value>
                    </member>
                    <member>
                        <name>response_timestamp</name>
                        <value>
                            <dateTime.iso8601>2023-02-08T20:12:24Z</dateTime.iso8601>
                        </value>
                    </member>
                    <member>
                        <name>api_status</name>
                        <value>
                            <int>500</int>
                        </value>
                    </member>
                    <member>
                        <name>errors</name>
                        <value>
                            <struct>
                                <member>
                                    <name>username</name>
                                    <value>
                                        <array>
                                            <data>
                                                <value>
                                                    <string>Email should be of the format someuser@example.com</string>
                                                </value>
                                            </data>
                                        </array>
                                    </value>
                                </member>
                            </struct>
                        </value>
                    </member>
                </struct>
            </value>
        </param>
    </params>
</methodResponse>
```

Invalid login

```xml
<?xml version="1.0" encoding="utf-8"?>
<methodResponse>
    <params>
        <param>
            <value>
                <struct>
                    <member>
                        <name>api_status</name>
                        <value>
                            <int>401</int>
                        </value>
                    </member>
                    <member>
                        <name>messages</name>
                        <value>
                            <array>
                                <data>
                                    <value>
                                        <string>Sorry, failed to log in.</string>
                                    </value>
                                </data>
                            </array>
                        </value>
                    </member>
                    <member>
                        <name>status</name>
                        <value>
                            <int>401</int>
                        </value>
                    </member>
                    <member>
                        <name>api</name>
                        <value>
                            <struct>
                                <member>
                                    <name>status</name>
                                    <value>
                                        <int>401</int>
                                    </value>
                                </member>
                            </struct>
                        </value>
                    </member>
                    <member>
                        <name>response_timestamp</name>
                        <value>
                            <dateTime.iso8601>2023-02-08T20:13:42Z</dateTime.iso8601>
                        </value>
                    </member>
                </struct>
            </value>
        </param>
    </params>
</methodResponse>
```

Successful login

```xml
<?xml version="1.0" encoding="utf-8"?>
<methodResponse>
    <params>
        <param>
            <value>
                <struct>
                    <member>
                        <name>sid</name>
                        <value>
                            <string>SID_HERE</string>
                        </value>
                    </member>
                    <member>
                        <name>api_status</name>
                        <value>
                            <int>200</int>
                        </value>
                    </member>
                    <member>
                        <name>response_timestamp</name>
                        <value>
                            <dateTime.iso8601>2023-02-08T20:15:04Z</dateTime.iso8601>
                        </value>
                    </member>
                    <member>
                        <name>status</name>
                        <value>
                            <int>200</int>
                        </value>
                    </member>
                </struct>
            </value>
        </param>
    </params>
</methodResponse>
```

Successfully drop a user

```xml
<?xml version="1.0" encoding="utf-8"?>
<methodResponse>
  <params>
      <param>
          <value>
              <struct>
                  <member>
                      <name>sid</name>
                      <value>
                          <string>SID_HERE</string>
                      </value>
                  </member>
                  <member>
                      <name>response_timestamp</name>
                      <value>
                          <dateTime.iso8601>2023-02-09T20:40:17Z</dateTime.iso8601>
                      </value>
                  </member>
                  <member>
                      <name>status</name>
                      <value>
                          <int>200</int>
                      </value>
                  </member>
                  <member>
                      <name>messages</name>
                      <value>
                          <array>
                              <data>
                                  <value>
                                      <string>User FIRSTNAME LASTNAME Deleted</string>
                                  </value>
                              </data>
                          </array>
                      </value>
                  </member>
                  <member>
                      <name>api_status</name>
                      <value>
                          <int>200</int>
                      </value>
                  </member>
              </struct>
          </value>
      </param>
  </params>
</methodResponse>
```