<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <link rel="stylesheet" type="text/css" charset="utf-8"
      href="${std.url('/static/css/current.css')}" />
    <title>Current</title>
</head>

<body>
    <h1>Profile Details</h1>

    <table>
        <tr>
            <th>Profile Name:</th>
            <td py:content="system['name']">Name goes here</td>
        </tr>
        <tr>
            <th>Profile ID:</th>
            <td py:content="system['profile_id']">ID Number</td>
        </tr>
        <tr>
            <th>Hostname:</th>
            <td py:content="system['hostname']">hostname</td>
        </tr>
        <tr>
            <th>IP Address:</th>
            <td py:content="system['ipaddr']">ipaddr</td>
        </tr>
        <tr>
            <th>Last Checkin Time:</th>
            <td py:content="system['checkin']">Time</td>
        </tr>
        <tr>
            <th>Subscribed Channels:</th>
            <td><span py:for="l in system['labels']">
                    <span py:replace="l">label-foo</span><br/></span>
            </td>
        </tr>
        <tr>
            <th>Number of Packages Needing Update:</th>
            <td py:content="system['num_old_packages']">All of them</td>
        </tr>
        <tr>
            <th>Running Kernel:</th>
            <td py:content="system['kernel']">kernel version</td>
        </tr>
        <tr>
            <th>System Uptime:</th>
            <td py:content="system['uptime']">time</td>
        </tr>
    </table>
    
</body>
</html>
