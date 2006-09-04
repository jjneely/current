<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>Current</title>
</head>

<body>
    <h1>Current Web Interface</h1>

    <p py:if="message != None" py:content="message"></p>

    <form method="post" action="/">
        <table>
            <tr>
                <td>User ID:</td>
                <td><input type="text" name="userid" /></td>
            </tr>
            <tr>
                <td>Password:</td>
                <td><input type="password" name="password" /></td>
            </tr>
        </table>
        <input type="submit" name="login" value="Log In" />
    </form>

</body>
</html>
