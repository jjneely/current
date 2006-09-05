<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:py="http://purl.org/kid/ns#" 
      py:extends="sitetemplate">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" 
      py:replace="''"/>
    <link rel="stylesheet" type="text/css" charset="utf-8"
      href="${std.url('/static/css/current.css')}" />
    <title>Your title goes here</title>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'">
    <!--<p align="center">
    <img src="${std.url('/static/images/current-2.jpg')}" 
      alt="Current" height="100" width="300" />
      </p>-->

    <div id="header">
      <p id="title">Current</p>
      <p id="headertext">Current Version 1.7.4</p>
                                
      <ul id="navibar">
        <li class="navlink">
          <a href="${std.url('/index')}">Main</a>
        </li>
        <li class="navlink">
          <a href="${std.url('/systems')}">Systems</a>
        </li>
        <li class="navlink">
          <a href="${std.url('/channels')}">Channels</a>
        </li>

        <li class="help">
          <a href="http://current.tigris.org">Current Home</a>
        </li>
      </ul>
      <div id="pageline"><hr style="display:none;" /></div>
    </div>

  <div id="content" py:content="item[:]"/>
  
  </body>
</html>
