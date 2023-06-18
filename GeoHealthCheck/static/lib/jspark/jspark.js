/**
 * Javascript Sparklines Library
 * Written By John Resig
 * http://ejohn.org/projects/jspark/
 * 
 * This work is tri-licensed under the MPL, GPL, and LGPL:
 * http://www.mozilla.org/MPL/
 * 
 * To use, place your data points within your HTML, like so:
 * <span class="sparkline">10,8,20,5...</span>
 *
 * in your CSS you might want to have the rule:
 * .sparkline { display: none }
 * so that non-compatible browsers don't see a huge pile of numbers.
 *
 * Finally, include this library in your header, like so:
 * <script language="javascript" src="jspark.js"></script>
 */

addEvent( window, "load", function() {
  var a = document.getElementsByTagName("*") || document.all;

  for ( var i = 0; i < a.length; i++ )
    if ( has( a[i].className, "sparkline" ) )
      sparkline( a[i] );
} );

function has(s,c) {
  var r = new RegExp("(^| )" + c + "\W*");
  return ( r.test(s) ? true : false );
}

function addEvent( obj, type, fn ) {
  if ( obj.attachEvent ) {
    obj['e'+type+fn] = fn;
    obj[type+fn] = function(){obj['e'+type+fn]( window.event );}
    obj.attachEvent( 'on'+type, obj[type+fn] );
  } else
    obj.addEventListener( type, fn, false );
}

function removeEvent( obj, type, fn ) {
  if ( obj.detachEvent ) {
    obj.detachEvent( 'on'+type, obj[type+fn] );
    obj[type+fn] = null;
  } else
    obj.removeEventListener( type, fn, false );
}


function sparkline(o) {
  var p = o.innerHTML.split(',');
  while ( o.childNodes.length > 0 )
    o.removeChild( o.firstChild );

  var nw = "auto";
  var nh = "auto";
  if ( window.getComputedStyle ) {
    nw = window.getComputedStyle( o, null ).width;
    nh = window.getComputedStyle( o, null ).height;
  }

  if ( nw != "auto" ) nw = nw.substr( 0, nw.length - 2 );
  if ( nh != "auto" ) nh = nh.substr( 0, nh.length - 2 );

  var f = 2;
  var w = ( nw == "auto" || nw == 0 ? p.length * f : nw - 0 );
  var h = ( nh == "auto" || nh == 0 ? "1em" : nh );

  var co = document.createElement("canvas");

  if ( co.getContext ) o.style.display = 'inline';
  else return false;

  co.style.height = h;
  co.style.width = w;
  co.width = w;
  o.appendChild( co );

  var h = co.offsetHeight;
  co.height = h;

  var min = 9999;
  var max = -1;

  for ( var i = 0; i < p.length; i++ ) {
    p[i] = p[i] - 0;
    if ( p[i] < min ) min = p[i];
    if ( p[i] > max ) max = p[i];
  }

  if ( co.getContext ) {
    var c = co.getContext("2d");
    c.strokeStyle = "red";
    c.lineWidth = 1.0;
    c.beginPath();

    for ( var i = 0; i < p.length; i++ ) {
      if ( i == 0 )
        c.moveTo( (w / p.length) * i, h - (((p[i] - min) / (max - min)) * h) );
      c.lineTo( (w / p.length) * i, h - (((p[i] - min) / (max - min)) * h) );
    }

    c.stroke();
    o.style.display = 'inline';
  }
}
