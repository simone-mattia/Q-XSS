<?php

$_SESSION['comment'][] = null;

if ($_SERVER["REQUEST_METHOD"] == "POST" && !empty(trim($_POST["comment"])))
{
    $_SESSION['comments'][] = $_POST["comment"];
}
?>
 
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.css">
    <style type="text/css">
        body{ font: 14px sans-serif; }
        .wrapper{ width: 350px; padding: 20px; }
    </style>
</head>
<body>
    <div class="wrapper">
        <h2>Post</h2>
        <?php 
            foreach ($_SESSION['comments'] as &$value) {
                echo "<b>Anonymous: </b>".$value;
                ?><br><?php
            }
        ?>
        <br><form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post">
            <div class="form-group">
                <label>Comments</label>
                <input type="text" name="comment" class="form-control" value="<?php echo $comment; ?>">
            </div> 
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Submit">
            </div>
        </form>
    </div>    
</body>
</html>