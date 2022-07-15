<?php
if (isset($_GET["name"])) {
    $name = substr(htmlentities($_GET['name']),1);
    echo "<b>Hi ".urldecode($name)."</b>";
}
?>