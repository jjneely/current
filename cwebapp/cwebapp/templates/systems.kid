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

    <p>The following systems are registered:</p>

    <table class="tabledata">
        <tr><th>Profile Name</th><th>Channel</th></tr>
        <tr py:for="i, system in enumerate(systems)" 
            class="${i%2 and 'oddrow' or 'evenrow'}">
            <td>
                <a href="" 
                    py:attrs="href='/systems/details?profileID=%s' % system['profile_id']"
                    py:content="system['name']">Name goes here</a>
            </td>
            <td><span py:for="l in system['labels']">
                    <span py:replace="l">label-foo</span><br/></span>
            </td>
        </tr>
    </table>
    
</body>
</html>
