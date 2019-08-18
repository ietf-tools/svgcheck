window.onload = function() {
    var x;
    var y;
    
    convertTrees();
    expandTree("diffRoot");

    // Get the element with id="defaultOpen" and click on it
    // document.getElementById("defaultOpen").click();
    // document.getElementById("defaultOpenR").click();

    resizeWindows();
    
    var leftHandle = document.getElementById("leftHandle");
    leftHandle.addEventListener('mousedown', initLeft, false);
    
    var rightHandle = document.getElementById("rightHandle");
    rightHandle.addEventListener('mousedown', initRight, false);

    //  Walk the style sheet

    var cssRules;
    var styles = {};
    
    for (var S = 0; S<document.styleSheets.length; S++) {
        if (document.styleSheets[S]['rules']) {
            cssRules = 'rules';
        }
        else if (document.styleSheets[S]['cssRules']) {
            cssRules = 'cssRules';
        }

        for (var R=0; R<document.styleSheets[S][cssRules].length; R++) {
            if (document.styleSheets[S][cssRules][R].selectorText &&
                document.styleSheets[S][cssRules][R].selectorText[0] == '.') {
                styles[document.styleSheets[S][cssRules][R].selectorText] = document.styleSheets[S][cssRules][R].style;
            }
        }
    }
    
    //  Copy down colors

    x = document.getElementsByTagName("SPAN")
    for (var i=0; i< x.length; i++) {
        if (x[i].className) {
            n = styles["." + x[i].className]
            if (!n) {
                continue;
            }
            if (n.color) {
                x[i].style.color = n.color;
            }
            if (n.backgroundColor) {
                x[i].style.backgroundColor = n.backgroundColor;
            }
        }
    }

    OnScrollCenter()
}


function initLeft(e) {
    window.addEventListener('mousemove', startResizingLeft, false);
    window.addEventListener('mouseup', stopResizingLeft, false);
    e.preventDefault();
}

function initRight(e) {
    window.addEventListener('mousemove', startResizingRight, false);
    window.addEventListener('mouseup', stopResizingRight, false);
    e.preventDefault();
}

function startResizingLeft(e) {
    var leftHandle = document.getElementById("leftHandle");
    var leftSource = document.getElementById("leftSource");

    //  Window width = 536 - mouse @ 555 = 20
    var ratio = (e.clientX - 20) / window.innerWidth;
    mySizeInfo.ratioLeft = Math.floor(ratio * 1000) / 10;
    console.log('mouse move event left' + leftSource.offsetWidth + ' --- ' + e.clientX + '  -- ' + ratio);
    resizeWindows();

    e.preventDefault();
    e.cancelBubble=true;
    return false;
}

function stopResizingLeft(e) {
    window.removeEventListener('mousemove', startResizingLeft, false);
    window.removeEventListener('mouseup', stopResizingLeft, false);
}

function startResizingRight(e) {
    var rightHandle = document.getElementById("rightHandle");
    var rightSource = document.getElementById("rightSource");

    //  Window width = 536 - mouse @ 555 = 20
    var ratio = 1 - ((e.clientX + 20) / window.innerWidth);
    mySizeInfo.ratioRight = Math.floor(ratio * 1000) / 10;
    console.log('mouse move event right' + leftSource.offsetWidth + ' --- ' + e.clientX + '  -- ' + ratio);
    resizeWindows();

    e.preventDefault();
    e.cancelBubble=true;
    return false;
}

function stopResizingRight(e) {
    window.removeEventListener('mousemove', startResizingRight, false);
    window.removeEventListener('mouseup', stopResizingRight, false);
}

window.onresize = resizeEvent;

function resizeEvent(e)
{
    resizeWindows()
}

var mySizeInfo = {
    "ratioLeft": 25,
    "ratioRight": 25,
    "hiddenSource": false
};


function resizeWindows()
{
    var x = window.innerWidth;
    var lx = 0;
    var rx = 0;
    var left = document.getElementById("leftContent");
    var right = document.getElementById("rightContent");
    if (mySizeInfo.hiddenSource) {
        left.style.width = "0px";
        right.style.width = "0px";
    }
    else {
        lx = Math.floor(x * mySizeInfo.ratioLeft / 100);
        left.style.width = lx + "px";

        rx = Math.floor(x * mySizeInfo.ratioRight / 100);
        right.style.width = rx + "px";
    }

    var center = document.getElementById("centerContent");
    center.style.width = (x - lx - rx - 60) + "px";

    console.log("resize - " + lx + " -- " + center.style.width + " -- " + rx)
}

function hideSidebars()
{
    var btn = document.getElementById("hideSource");
    var visible = true;
    if (btn.textContent == "Hide Source Files") {
        btn.textContent = "Show Source Files";
        mySizeInfo.hiddenSource = true;
    }
    else {
        btn.textContent = "Hide Source Files";
        mySizeInfo.hiddenSource = false;
    }

    resizeWindows()
}

function selectChange( id ) {
    var selectId = id + "FileNames"
    var node = document.getElementById( selectId );

    if (node && node.tagName == "SELECT") {
        var value = node.options[node.selectedIndex].value;

        console.log("--> select Change => " + value)
        
        // Declare variables
        var i, tabcontent, tablinks;
        var tabsId = id + "Source"
        
        //  Get all elements w/ class='tabcontent' and hide them
        tabcontent = document.getElementById(tabsId).getElementsByClassName("tabcontent");
        for (i=0; i<tabcontent.length; i++) {
            tabcontent[i].style.display="none";
        }

        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(value).style.display = "block";
    }
}
        
function openLeftFile(evt, fileName) {
    // Declare variables
    var i, tabcontent, tablinks;
    //  Get all elements w/ class='tabcontent' and hide them
    tabcontent = document.getElementById("leftContent").getElementsByClassName("tabcontent");
    for (i=0; i<tabcontent.length; i++) {
        tabcontent[i].style.display="none";
    }
    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementById("leftContent").getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(fileName).style.display = "block";
    evt.currentTarget.className += " active";
}

function openRightFile(evt, fileName) {
    // Declare variables
    var i, tabcontent, tablinks;
    //  Get all elements w/ class='tabcontent' and hide them
    tabcontent = document.getElementById("rightSource").getElementsByClassName("tabcontent");
    for (i=0; i<tabcontent.length; i++) {
        tabcontent[i].style.display="none";
    }
    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementById("rightContent").getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(fileName).style.display = "block";
    evt.currentTarget.className += " active";
}
                    
function sync2here(leftFile, leftLine, rightFile, rightLine)
{
    if (leftFile != -1) {
        leftDiv = document.getElementById("leftContent")
    }
}

function OnScrollCenter()
{
    var el2 = XXX()
                    
    if (el2.hasAttribute('whereLeft')) {
        var tag = el2.attributes['whereLeft'].value;
        var fileNum = "L_File" + tag.substring(tag.indexOf('_')+1);
        console.log('** whereLeft -> ' + fileNum + ' ** ' + tag)
        
        document.getElementById('leftFileNames').value = fileNum;
        selectChange('left')
        
        document.getElementById(tag).scrollIntoView();
    }                
    if (el2.hasAttribute('whereRight')) {
        var tag = el2.attributes['whereRight'].value;
        var fileNum = "R_File" + tag.substring(tag.indexOf('_')+1);
        console.log('** whereRight -> ' + fileNum + ' ** ' + tag)
        
        document.getElementById('rightFileNames').value = fileNum;
        selectChange('right')
        
        document.getElementById(tag).scrollIntoView();
    }                
}

function XXX()
{
    var xxx = document.getElementById("centerColumn");
    var scroll = xxx.scrollTop;
    var elements = xxx.getElementsByTagName("li");
    var el;
    for (var i=0; i<elements.length; i++) {
        el = elements[i];
        if (el.offsetTop > 0 && isElementVisible(el)) {
            return el;
        }
    }
    return null;
}

function isElementVisible(el) {
    var rect     = el.getBoundingClientRect(),
        vWidth   = window.innerWidth || document.documentElement.clientWidth,
        vHeight  = window.innerHeight || document.documentElement.clientHeight,
        efp      = function (x, y) { return document.elementFromPoint(x, y) };     

    // Return false if it's not in the viewport
    if (rect.right < 0 || rect.bottom < 0 
            || rect.left > vWidth || rect.top > vHeight)
        return false;

    // Return true if any of its four corners are visible
    return (
          el.contains(efp(rect.left,  rect.top))
      ||  el.contains(efp(rect.right, rect.top))
      ||  el.contains(efp(rect.right, rect.bottom))
      ||  el.contains(efp(rect.left,  rect.bottom))
    );
}                    

//  Begin mktree.js

/**
 * Copyright (c)2005-2009 Matt Kruse (javascripttoolbox.com)
 * 
 * Dual licensed under the MIT and GPL licenses. 
 * This basically means you can use this code however you want for
 * free, but don't claim to have written it yourself!
 * Donations always accepted: http://www.JavascriptToolbox.com/donate/
 * 
 * Please do not link to the .js files on javascripttoolbox.com from
 * your site. Copy the files locally to your server instead.
 * 
 */
/*
This code is inspired by and extended from Stuart Langridge's aqlist code:
    http://www.kryogenix.org/code/browser/aqlists/
    Stuart Langridge, November 2002
    sil@kryogenix.org
    Inspired by Aaron's labels.js (http://youngpup.net/demos/labels/) 
    and Dave Lindquist's menuDropDown.js (http://www.gazingus.org/dhtml/?id=109)
*/

// Automatically attach a listener to the window onload, to convert the trees
// addEvent(window,"load",convertTrees);

// Utility function to add an event listener
function addEvent(o,e,f){
  if (o.addEventListener){ o.addEventListener(e,f,false); return true; }
  else if (o.attachEvent){ return o.attachEvent("on"+e,f); }
  else { return false; }
}

// utility function to set a global variable if it is not already set
function setDefault(name,val) {
  if (typeof(window[name])=="undefined" || window[name]==null) {
    window[name]=val;
  }
}

// Full expands a tree with a given ID
function expandTree(treeId) {
  var ul = document.getElementById(treeId);
  if (ul == null) { return false; }
  expandCollapseList(ul,nodeOpenClass);
}

// Fully collapses a tree with a given ID
function collapseTree(treeId) {
  var ul = document.getElementById(treeId);
  if (ul == null) { return false; }
  expandCollapseList(ul,nodeClosedClass);
}

// Expands enough nodes to expose an LI with a given ID
function expandToItem(treeId,itemId) {
  var ul = document.getElementById(treeId);
  if (ul == null) { return false; }
  var ret = expandCollapseList(ul,nodeOpenClass,itemId);
  if (ret) {
    var o = document.getElementById(itemId);
    if (o.scrollIntoView) {
      o.scrollIntoView(false);
    }
  }
}

// Performs 3 functions:
// a) Expand all nodes
// b) Collapse all nodes
// c) Expand all nodes to reach a certain ID
function expandCollapseList(ul,cName,itemId) {
  if (!ul.childNodes || ul.childNodes.length==0) { return false; }
  // Iterate LIs
  for (var itemi=0;itemi<ul.childNodes.length;itemi++) {
    var item = ul.childNodes[itemi];
    if (itemId!=null && item.id==itemId) { return true; }
    if (item.nodeName == "LI") {
      // Iterate things in this LI
      var subLists = false;
      for (var sitemi=0;sitemi<item.childNodes.length;sitemi++) {
        var sitem = item.childNodes[sitemi];
        if (sitem.nodeName=="UL") {
          subLists = true;
          var ret = expandCollapseList(sitem,cName,itemId);
          if (itemId!=null && ret) {
            item.className=cName;
            return true;
          }
        }
      }
      if (subLists && itemId==null) {
        item.className = cName;
      }
    }
  }
}

// Search the document for UL elements with the correct CLASS name, then process them
function convertTrees() {
  setDefault("treeClass","mktree");
  setDefault("nodeClosedClass","liClosed");
  setDefault("nodeOpenClass","liOpen");
  setDefault("nodeBulletClass","liBullet");
  setDefault("nodeLinkClass","bullet");
  setDefault("preProcessTrees",true);
  if (preProcessTrees) {
    if (!document.createElement) { return; } // Without createElement, we can't do anything
    var uls = document.getElementsByTagName("ul");
    if (uls==null) { return; }
    var uls_length = uls.length;
    for (var uli=0;uli<uls_length;uli++) {
      var ul=uls[uli];
      if (ul.nodeName=="UL" && ul.className==treeClass) {
        processList(ul);
      }
    }
  }
}

function treeNodeOnclick() {
  this.parentNode.className = (this.parentNode.className==nodeOpenClass) ? nodeClosedClass : nodeOpenClass;
  return false;
}
function retFalse() {
  return false;
}
// Process a UL tag and all its children, to convert to a tree
function processList(ul) {
  if (!ul.childNodes || ul.childNodes.length==0) { return; }
  // Iterate LIs
  var childNodesLength = ul.childNodes.length;
  for (var itemi=0;itemi<childNodesLength;itemi++) {
    var item = ul.childNodes[itemi];
    if (item.nodeName == "LI") {
      // Iterate things in this LI
      var subLists = false;
      var itemChildNodesLength = item.childNodes.length;
      for (var sitemi=0;sitemi<itemChildNodesLength;sitemi++) {
        var sitem = item.childNodes[sitemi];
        if (sitem.nodeName=="UL") {
          subLists = true;
          processList(sitem);
        }
      }
      var s= document.createElement("SPAN");
      var t= '\u00A0'; // &nbsp;
      s.className = nodeLinkClass;
      if (subLists) {
        // This LI has UL's in it, so it's a +/- node
        if (item.className==null || item.className=="") {
          item.className = nodeClosedClass;
        }
        // If it's just text, make the text work as the link also
        if (item.firstChild.nodeName=="#text") {
          t = t+item.firstChild.nodeValue;
          item.removeChild(item.firstChild);
        }
        s.onclick = treeNodeOnclick;
      }
      else {
        // No sublists, so it's just a bullet node
        item.className = nodeBulletClass;
        s.onclick = retFalse;
      }
      s.appendChild(document.createTextNode(t));
      item.insertBefore(s,item.firstChild);
    }
  }
}


function expandDiffs(itemId) {
    var ul = document.getElementById(itemId)
    if (ul == null) { return false; }
    expandCollapseDiffs(ul)
}

function expandCollapseDiffs(node) {
    if (!node.childNodes || node.childNodes.length == 0) {
	if (node.classList && (node.classList.contains("right") || node.classList.contains("left"))) {
	    return true;
	}
	return false;
    }

    var doExpand = (node.classList && (node.classList.contains("right") || node.classList.contains("left")));

    for (var itemi=0; itemi<node.childNodes.length; itemi++) {
	var item = node.childNodes[itemi];

	doExpand |= expandCollapseDiffs(item);
	
    }

    if (node.nodeName == "LI" && !node.classList.contains("liBullet")) {
	node.className = doExpand ? nodeOpenClass : nodeClosedClass;
    }
    return doExpand;
}


//  End mktree.js
