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
    <h1>Current Web Interface</h1>

    <p>Channels:</p>

    <table class="tabledata">
        <tr><th>Name</th><th>Label</th></tr>
        <tr py:for="i, channel in enumerate(channels)" 
            class="${i%2 and 'oddrow' or 'evenrow'}">
            <td><a href="" py:content="channel['name']"
                   py:attrs="href='/channels/detail?label='+channel['label']">
                   Name goes here</a>
           </td>
           <td><a href="" py:content="channel['label']"
                  py:attrs="href='/channels/detail?label='+channel['label']">
                  Channel-label</a>
          </td>
        </tr>
    </table>
    
</body>
</html>
