### This script creates a CSV file where MAC address ranges are converted to IPv6 networks format.
Data from this file is used in [Graylog](https://graylog.org) lookup tables for use in your pipelines to add or create a vendor MAC data field in your logs.

1. run the python script to create CSV file with MAC-vendor fields  
`python ./parse-lookup-table-oui-ieee.py`

2. define new lookup table in Graylog to use in your pipelines.
- Create a new data adapter for the lookup table
```
Type:            CSV file
Name:            mac-oui
File path:       /etc/graylog/lookup-table/oui-ieee.csv
Separator:       ,
Quote character: "
Key column:      mac
Value column:    vendor
Check interval:  N sec
CIDR lookup:     yes
```
- For best performance you should create a new cache for the lookup table
```
Name:         mac-oui
```
- Create a new lookup table
```
Name:         mac-oui
Data Adapter: mac-oui
Cache:        mac-oui
```

3. Third: use this lookup table in your pipelines

###### Pipeline rule example:
```
rule "MAC-vendor"
when has_field ("mac")
  OR has_field ("source-mac")
  OR has_field ("destination-mac")
then

  // normalize all MAC address formats to aabbccddeeff
  let normalized = {
    `mac`             : regex_replace("[\\:\\-\\.]",lowercase(to_string(grok("^([01]:)?%{MAC:M}$",to_string($message."mac"),            true)."M")),""),
    `source-mac`      : regex_replace("[\\:\\-\\.]",lowercase(to_string(grok("^([01]:)?%{MAC:M}$",to_string($message."source-mac"),     true)."M")),""),
    `destination-mac` : regex_replace("[\\:\\-\\.]",lowercase(to_string(grok("^([01]:)?%{MAC:M}$",to_string($message."destination-mac"),true)."M")),"")
  };

  // convert all normalized MAC addresses to IPv6 format and use lookup table "mac-oui" to search MAC-vendor name
  let vendors = {
    `mac`             : to_string(lookup_value("mac-oui",concat(regex_replace("(.{4})", to_string(normalized."mac"),             "$1\\:", true), ":"))),
    `source-mac`      : to_string(lookup_value("mac-oui",concat(regex_replace("(.{4})", to_string(normalized."source-mac"),      "$1\\:", true), ":"))),
    `destination-mac` : to_string(lookup_value("mac-oui",concat(regex_replace("(.{4})", to_string(normalized."destination-mac"), "$1\\:", true), ":")))
  };

  // write MAC-vendor field if any
  set_fields (
    fields: vendors,
    suffix: "-vendor"
  );

end
```
