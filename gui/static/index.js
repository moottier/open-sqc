// Production steps of ECMA-262, Edition 6, 22.1.2.1
if (!Array.from) {
    Array.from = (function () {
        var toStr = Object.prototype.toString;
        var isCallable = function (fn) {
            return typeof fn === 'function' || toStr.call(fn) === '[object Function]';
        };
        var toInteger = function (value) {
            var number = Number(value);
            if (isNaN(number)) {
                return 0;
            }
            if (number === 0 || !isFinite(number)) {
                return number;
            }
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
    function () {
        return new XMLHttpRequest()
    },
    function () {
        return new ActiveXObject("Msxml3.XMLHTTP")
    },
    function () {
        return new ActiveXObject("Msxml2.XMLHTTP.6.0")
    },
    function () {
        return new ActiveXObject("Msxml2.XMLHTTP.3.0")
    },
    function () {
        return new ActiveXObject("Msxml2.XMLHTTP")
    },
    function () {
        return new ActiveXObject("Microsoft.XMLHTTP")
    }
];


function createXMLHTTPObject() {
    // TODO add error handling
    var xmlhttp = false;
    for (var i = 0; i < XMLHttpFactories.length; i++) {
        try {
            xmlhttp = XMLHttpFactories[i]();
        } catch (e) {
            continue;
        }
        break;
    }
    return xmlhttp;
}

document.addEventListener('DOMContentLoaded', function () {
    setChartInterFaceListeners();

    // input elem listener
    var inputElem = document.getElementById('load');
    inputElem.addEventListener('change', handleFiles, false);
}, false);

function setChartInterFaceListeners(){
    // select change listeners
    var fileSelectElems = document.getElementById('chart-interface').getElementsByTagName('select');
    Array.from(fileSelectElems).forEach(function (fileSelectElem) {
        fileSelectElem.onchange = chartSelectChangeHandler;
    });

    // file-name click listeners
    var fileNameElems = document.getElementById('chart-interface').getElementsByClassName('chart-name');
    Array.from(fileNameElems).forEach(function (fileNameElem) {
        fileNameElem.onclick = chartNameClickHandler;
    });

    // up arrow listeners
    var upArrowElems = document.getElementById('chart-interface').getElementsByClassName('up arrow');
    Array.from(upArrowElems).forEach(function (upArrowElem) {
        upArrowElem.onclick = chartUpArrowClickHandler;
    });

    // down arrow listeners
    var downArrowElems = document.getElementById('chart-interface').getElementsByClassName('down arrow');
    Array.from(downArrowElems).forEach(function (downArrowElem) {
        downArrowElem.onclick = chartDownArrowClickHandler;
    });

    // delete listeners
    var deleteElems = document.getElementById('chart-interface').getElementsByClassName('delete');
    Array.from(deleteElems).forEach(function (deleteElem) {
        deleteElem.onclick = chartDeleteClickHandler;
    });
}

function handleFiles(event) {
    var fileList = event.target.files;
    Array.from(fileList).forEach(function(file) {
        sendFile(file);
    });
}

function sendFile(file) {
    var request = createXMLHTTPObject();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            var elem = document.getElementById('chart-interface');
            elem.innerHTML = this.responseText;
            setChartInterFaceListeners();
        }
    };
    var form = new FormData();
    form.append('userfile', file, file.name);
    request.open('POST', '/_upload');
    request.send(form);
}


function chartSelectChangeHandler(ev) {
    var request = createXMLHTTPObject();
    var selectedType = ev.target.value;
    var chartTitle = ev.target.name;
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            if (JSON.parse(this.responseText).updatePlot) {
                showPlot(chartTitle);
            }
        }
    };
    request.open('POST', '/_set_chart_type'); // TODO me
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(
        JSON.stringify(
        {
            'selectedType': selectedType,
            'chartTitle': chartTitle,
            'isCurrentlyVisible': isCurrentlyVisible(chartTitle)
        }
        )
    );
}

function isCurrentlyVisible(chartTitle){
    return (document.getElementById('make_plot-title').innerHTML === chartTitle);
}

function showPlot(chartTitle) {
    var request = createXMLHTTPObject();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
                document.getElementById('make_plot-interface').innerHTML = this.responseText;
        }
    };
    request.open('POST', '/show_chart');
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartTitle': chartTitle}));
}


function chartNameClickHandler(ev) {
    showPlot(ev.target.parentElement.parentElement.id);
}


function swapSibling(node1, node2) {
    node1.parentNode.replaceChild(node1, node2);
    node1.parentNode.insertBefore(node2, node1);
}


function chartUpArrowClickHandler(ev) {
    var request = createXMLHTTPObject();
    var callingNode = ev.target.parentNode.parentNode;
    var nodeAbove = callingNode.previousElementSibling;
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            if (JSON.parse(this.responseText).success) {
                nodeAbove && swapSibling(nodeAbove, callingNode);
            }
        }
    };
    var chartTitle = ev.target.parentElement.parentElement.id;
    request.open('POST', '/_move_chart', true);
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartTitle': chartTitle, 'moveUp': true}));
}


function chartDownArrowClickHandler(ev) {
    var request = createXMLHTTPObject();
    var callingNode = ev.target.parentNode.parentNode;
    var nodeBelow = callingNode.nextElementSibling;
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            if (JSON.parse(this.responseText).success) {
                nodeBelow && swapSibling(callingNode, nodeBelow);
            }
        }
    };
    var chartTitle = ev.target.parentElement.parentElement.id;
    request.open('POST', '/_move_chart', true);
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartTitle': chartTitle, 'moveUp': false}));
}


function chartDeleteClickHandler(ev) {
    var request = createXMLHTTPObject();
    var deleteNode = ev.target.parentNode.parentNode;
    var deleteParentNode = deleteNode.parentNode;
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            JSON.parse(this.responseText).success && deleteParentNode.removeChild(deleteNode);
            // TODO
            // anyway to store this HTML in variable that can be accessed
            // by both Jinja and browser
            if (!deleteParentNode.children.length) {
                deleteParentNode.innerHTML =
                    ['<div class="container" id="{{ file }}">',
                        '<span>',
                        '<p>Nothing loaded. Click below to load</p>',
                        '</span>',
                        '</div>'
                    ].join('\n');
                }
        }
    };
    var chartTitle = ev.target.parentElement.parentElement.id;
    request.open('POST', '/_delete_chart', true);
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(JSON.stringify({'chartTitle': chartTitle}));
}
