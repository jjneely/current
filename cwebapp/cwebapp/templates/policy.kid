<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <link rel="stylesheet" type="text/css" charset="utf-8"
      href="${tg.url('/static/css/current.css')}" />
    <title>Current</title>
</head>

<body>
    <h1>Client Hieracracy and Permissions</h1>

    <p>My OU is <span py:replace="OU">Foo</span></p>

    <table class="tabledata">
        <tr><th>OU Label</th><th>Description</th><th>Attached Clients</th></tr>
        <tr py:for="i, row in enumerate(tree)" 
            class="${i%2 and 'oddrow' or 'evenrow'}">

            <td>
                <span py:replace="'&nbsp;&nbsp;&nbsp;'*row['depth']"></span>
                <img src="${tg.url('/static/images/favicon.ico')}" />
                <span py:replace="row['label']">OU Label</span>
            </td>

            <td py:content="row['description']">
            </td>

            <td py:content="row['num_clients']">
            </td>

        </tr>
    </table>
    
</body>
</html>
