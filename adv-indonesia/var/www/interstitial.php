<?
//The time of interstitial display is configured here.
header('Refresh: 10; URL=' . $_GET['url']);
?>

<html>
<head>
<title>Maximada AD</title>
</head>
<body>
<a href="<?=$_GET['url']?>">close</a>

<center>
	<img src="interstial.png" />
</center>

</body>
</html>
