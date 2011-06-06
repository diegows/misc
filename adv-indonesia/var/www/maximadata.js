//////CONFIG//////

//The url of the interstitial page.
var interstitial_url = 'http://202.51.56.106/interstitial.php?url=';

//The url of the iframe content of the advertising at the bottom
var bottom_ad_url = 'http://202.51.56.106/bottom-ad.html';

//Cookie stored in each domain to control the frequency of the interstitial.
var cookie_name = 'maximadataad';

//This defines the frequency of advertising in the same domain.
//The value is in seconds.
var cookie_timeout = 120;

//Frequency: 1/n, is the probability of the interstial.
//For example, frequency=1 you will see interstatial always, when you go
//to a new site. If frequency is 2, you will have a probability of 50% to
//see the advertising.
var frequency = 2;

////// END CONFIG //////

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

if(window.top == window.self){
  var ad = getCookie(cookie_name);
  if ((ad == null || ad == "") && Math.floor(Math.random()*frequency) == 0 ){
    var url = interstitial_url + encodeURIComponent(window.location);
    setCookie(cookie_name, 'true', cookie_timeout);
    window.location = url;
  }
  document.write('<iframe id="maximadatabottom" src="' + bottom_ad_url + '">X</iframe>');
}

$(document).ready(
function () {
    var adsHeight = $('#maximadatabottom').height();
    var currentMarginBottom = Number($('body').css('margin-bottom').replace('px', ''));
    
    $('body').css({'margin-bottom': adsHeight + currentMarginBottom});
});
