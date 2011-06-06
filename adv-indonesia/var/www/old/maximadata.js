//List of images with advertising and their links.
//If you have X adimsgs you MUST have X adlinks or it will fail.
var adimgs = [ "http://202.51.56.106/5564766_1.jpg" ];
var adlinks = [ "http://www.google.com.ar" ];

//How many milliseconds the advertising will be displayed
var duration = 10000;

//Frequency: 1/n
frequency = 1;

var selected = Math.floor (Math.random () * adimgs.length);
var adimg = adimgs[selected];
var adlink = adlinks[selected];

function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

function pmyr_ok(){
	document.getElementById('pmyr_div').style.visibility="hidden";
}

function setCookie(c_name,value,exsecs)
{
var exdate=new Date();
exdate.setTime(exdate.getTime() + exsecs * 1000);
var c_value=escape(value) + ((exsecs==null) ? "" : "; expires="+exdate.toUTCString());
document.cookie=c_name + "=" + c_value;
}

function getCookie(c_name)
{
var i,x,y,ARRcookies=document.cookie.split(";");
for (i=0;i<ARRcookies.length;i++)
{
  x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
  y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
  x=x.replace(/^\s+|\s+$/g,"");
  if (x==c_name)
    {
    return unescape(y);
    }
  }
}

//setTimeout('pmyr_ok();', duration);

if(window.top == window.self){
/*	if(Math.floor(Math.random()*frequency)==0){
		document.write('<div id="pmyr_div"><a href="' + adlink + '"><img src="' + adimg + '" /></a><a onclick="pmyr_ok()" style="cursor:pointer;position: absolute;top:0;left:0;">close</a></div>');
}*/

	var ad = getCookie("maximadataad");
	if (ad == null || ad == ""){
	var url = 'http://202.51.56.106/interstitial.php?url=' + encodeURIComponent(window.location);
	setCookie("maximadataad", 'true', 40);
	window.location = url;
	}
	document.write('<div id="maximadatabottom">ADVERSITING GOES HERE!!!!</div>');
	}
