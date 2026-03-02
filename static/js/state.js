var state = {
  files: [],
  urls: [],
  lang: "en",
  numTags: 10,
  model: "clip-openai",
  mode: "clip",
  running: false,
  completed: 0,
  failed: 0,
  inputMode: "file",
  startIndex: 1,
  modelReady: false,
  modelLoading: false
};

var fileInput = document.getElementById("fileInput");
var folderInput = document.getElementById("folderInput");
var runButton = document.getElementById("runButton");
var stopButton = document.getElementById("stopButton");
var retryAllButton = document.getElementById("retryAllButton");
var clearButton = document.getElementById("clearButton");
var exportDropdown = document.getElementById("exportDropdown");
var exportDropdownButton = document.getElementById("exportDropdownButton");
var exportDropdownMenu = document.getElementById("exportDropdownMenu");
var threadsInput = document.getElementById("threadsInput");
var startIndexInput = document.getElementById("startIndexInput");
var customVocabInput = document.getElementById("customVocabInput");
var modelSelect = document.getElementById("modelSelect");
var modeSelect = document.getElementById("modeSelect");
var summaryText = document.getElementById("summaryText");
var resultSummary = document.getElementById("resultSummary");
var gallery = document.getElementById("gallery");
var statusDot = document.getElementById("statusDot");
var statusText = document.getElementById("statusText");
var queueHint = document.getElementById("queueHint");
var urlInput = document.getElementById("urlInput");
var fileModeArea = document.getElementById("fileModeArea");
var urlModeArea = document.getElementById("urlModeArea");
var modeFileBtn = document.getElementById("modeFileBtn");
var modeUrlBtn = document.getElementById("modeUrlBtn");

