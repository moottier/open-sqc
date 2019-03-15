// Production steps of ECMA-262, Edition 6, 22.1.2.1
if (!Array.from) {
    Array.from = (function () {
      var toStr = Object.prototype.toString;
      var isCallable = function (fn) {
        return typeof fn === 'function' || toStr.call(fn) === '[object Function]';
      };
      var toInteger = function (value) {
        var number = Number(value);
        if (isNaN(number)) { return 0; }
        if (number === 0 || !isFinite(number)) { return number; }
        return (number > 0 ? 1 : -1) * Math.floor(Math.abs(number));
      };
      var maxSafeInteger = Math.pow(2, 53) - 1;
      var toLength = function (value) {
        var len = toInteger(value);
        return Math.min(Math.max(len, 0), maxSafeInteger);
      };
  
      // The length property of the from method is 1.
      return function from(arrayLike/*, mapFn, thisArg */) {
        // 1. Let C be the this value.
        var C = this;
  
        // 2. Let items be ToObject(arrayLike).
        var items = Object(arrayLike);
  
        // 3. ReturnIfAbrupt(items).
        if (arrayLike == null) {
          throw new TypeError('Array.from requires an array-like object - not null or undefined');
        }
  
        // 4. If mapfn is undefined, then let mapping be false.
        var mapFn = arguments.length > 1 ? arguments[1] : void undefined;
        var T;
        if (typeof mapFn !== 'undefined') {
          // 5. else
          // 5. a If IsCallable(mapfn) is false, throw a TypeError exception.
          if (!isCallable(mapFn)) {
            throw new TypeError('Array.from: when provided, the second argument must be a function');
          }
  
          // 5. b. If thisArg was supplied, let T be thisArg; else let T be undefined.
          if (arguments.length > 2) {
            T = arguments[2];
          }
        }
  
        // 10. Let lenValue be Get(items, "length").
        // 11. Let len be ToLength(lenValue).
        var len = toLength(items.length);
  
        // 13. If IsConstructor(C) is true, then
        // 13. a. Let A be the result of calling the [[Construct]] internal method 
        // of C with an argument list containing the single item len.
        // 14. a. Else, Let A be ArrayCreate(len).
        var A = isCallable(C) ? Object(new C(len)) : new Array(len);
  
        // 16. Let k be 0.
        var k = 0;
        // 17. Repeat, while k < len… (also steps a - h)
        var kValue;
        while (k < len) {
          kValue = items[k];
          if (mapFn) {
            A[k] = typeof T === 'undefined' ? mapFn(kValue, k) : mapFn.call(T, kValue, k);
          } else {
            A[k] = kValue;
          }
          k += 1;
        }
        // 18. Let putStatus be Put(A, "length", len, true).
        A.length = len;
        // 20. Return A.
        return A;
      };
    }());
  }


var XMLHttpFactories = [
    function () {return new XMLHttpRequest()},
    function () {return new ActiveXObject("Msxml3.XMLHTTP")},
    function () {return new ActiveXObject("Msxml2.XMLHTTP.6.0")},
    function () {return new ActiveXObject("Msxml2.XMLHTTP.3.0")},
    function () {return new ActiveXObject("Msxml2.XMLHTTP")},
    function () {return new ActiveXObject("Microsoft.XMLHTTP")}
];

function createXMLHTTPObject() {
    // TODO add error handling
    var xmlhttp = false;
    for (var i=0;i<XMLHttpFactories.length;i++) {
        try {
            xmlhttp = XMLHttpFactories[i]();
        }
        catch (e) {
            continue;
        }
        break;
    }
    return xmlhttp;
}

document.addEventListener('DOMContentLoaded', function(){
    // select change listeners
    var fileSelectElems = document.getElementById('chart-interface').getElementsByTagName('select');
    Array.from(fileSelectElems).forEach(function(fileSelectElem) {
        fileSelectElem.onchange = chartSelectChangeHandler;
    });

    // file-name click listeners
    var fileNameElems = document.getElementById('chart-interface').getElementsByClassName('chart-name');
    Array.from(fileNameElems).forEach(function(fileNameElem){
        fileNameElem.onclick = chartNameClickHandler;
    });

    // up arrow listeners
    var upArrowElems = document.getElementById('chart-interface').getElementsByClassName('up arrow');
    Array.from(upArrowElems).forEach(function(upArrowElem) {
        upArrowElem.onclick = chartUpArrowClickHandler;
    });

    // down arrow listeners
    var downArrowElems = document.getElementById('chart-interface').getElementsByClassName('down arrow');
    Array.from(downArrowElems).forEach(function(downArrowElem) {
        downArrowElem.onclick = chartDownArrowClickHandler;
    });

    // delete listeners
    var deleteElems = document.getElementById('chart-interface').getElementsByClassName('delete');
    Array.from(deleteElems).forEach(function(deleteElem) {
        deleteElem.onclick = chartDeleteClickHandler;
    });

}, false);


function showChart(chartTitle, chartPlotUrl) {
    var chartDisplayElem = document.getElementById('chart');
    var chartTitleElem = document.getElementById('chart-title');
    chartTitleElem.innerText = chartTitle;    
    chartDisplayElem.innerHTML = ['<img src=', chartPlotUrl, '>'].join('');
}

function showChartBlank() {
    var chartDisplayElem = document.getElementById('chart');
    var chartTitleElem = document.getElementById('chart-title');
    chartTitleElem.innerText = "Click a Chart name to load a chart";    
    chartDisplayElem.innerHTML = null;
}

function chartSelectChangeHandler(ev) {
    var request = createXMLHTTPObject();
    request.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var resText = JSON.parse(this.responseText);
            showChart(resText.chartTitle, resText.chartPlotUrl);            
            };
        };

    var chartType = ev.target.value;
    var chartSourceFileName = ev.target.previousElementSibling.innerText;
    request.open('POST', '/_select_chart_change');
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartType': chartType, 'chartSourceFileName': chartSourceFileName}));
};


function chartNameClickHandler(ev) {
    var request = createXMLHTTPObject();
    request.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var resText = JSON.parse(this.responseText);
            showChart(resText.chartTitle, resText.chartPlotUrl);     
        };
    };

    var chartType = ev.target.nextElementSibling.selectedOptions[0].value;
    var chartSourceFileName = ev.target.innerText;
    request.open('POST', '/_select_chart_change');
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartType': chartType, 'chartSourceFileName': chartSourceFileName}));
};


function swapSibling(node1, node2) {
    node1.parentNode.replaceChild(node1, node2);
    node1.parentNode.insertBefore(node2, node1); 
};


function getNodeFromParentChildrenByClass(parent, cls){
    var lostChild = null;
    for (var i = 0; i < parent.childNodes.length; i++) {
        if (parent.childNodes[i].className == cls) {
            lostChild = parent.childNodes[i];
            break;
        }
    }
    return lostChild;
}


function getNodeFromParentChildrenById(parent, id){
    var lostChild = null;
    for (var i = 0; i < parent.childNodes.length; i++) {
        if (parent.childNodes[i].id == id) {
            lostChild = parent.childNodes[i];
            break;
        }
    }
    return lostChild;
}


function chartUpArrowClickHandler(ev) {
    var callingNode = ev.target.parentNode.parentNode;
    var nodeAbove = callingNode.previousElementSibling;
    console.log(nodeAbove);
    nodeAbove && swapSibling(nodeAbove, callingNode);
};


function chartDownArrowClickHandler(ev) {
    var callingNode = ev.target.parentNode.parentNode;
    var nodeBelow = callingNode.nextElementSibling;
    console.log(nodeBelow);
    nodeBelow && swapSibling(callingNode, nodeBelow);
};


function chartDeleteClickHandler(ev) {
    var deleteNode = ev.target.parentNode.parentNode;
    var deleteParentNode = deleteNode.parentNode;
    deleteParentNode.removeChild(deleteNode);

    // TODO 
    // anyway to store this HTML in variable that can be accessed
    // by both Jinja and browser
    if (!deleteParentNode.children.length) {
        deleteParentNode.innerHTML = 
        ['<div class="container loaded-file" id="{{ file }}">',
         '<span>',
         '<p>Nothing loaded. Click below to load</p>',
         '</span>',
         '</div>'
        ].join('\n');
    };
};
