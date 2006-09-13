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
    <h1>Channel Details</h1>

    <table>
        <tr>
            <th>Channel Name:</th>
            <td py:content="channel['name']">Name goes here</td>
        </tr>
        <tr>
            <th>Label:</th>
            <td py:content="channel['label']">label-foo-i386</td>
        </tr>
        <tr>
            <th>Description:</th>
            <td py:content="channel['description']">ID Number</td>
        </tr>
        <tr>
            <th>Arch:</th>
            <td py:content="channel['arch']">i786</td>
        </tr>
        <tr>
            <th>OS Release:</th>
            <td py:content="channel['osrelease']">i786</td>
        </tr>
        <tr>
            <th>Last Update Timestamp:</th>
            <td py:content="channel['lastupdate']">i786</td>
        </tr>
        <tr>
            <th>Base Channel:</th>
            <td py:if="channel['base']">True</td>
            <td py:if="not channel['base']">False</td>
        </tr>
    </table>
    
</body>
</html>
