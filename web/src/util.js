
// Converts a simple query string a=b&c=d&e=f into a javascript object
// Doesn't allow for keys with more than one - last value overwrites previous values for a given key
export function parseParams(queryString) {
  var params = {}
  var regex = /([^&=]+)=([^&]*)/g
  var m

  while(true) {
    m = regex.exec(queryString)
    if(!m) break
    params[decodeURIComponent(m[1])] = decodeURIComponent(m[2])
  }
  return params
}

export function encodeParams(params) {
  return Object.entries(params)
    .map(p => encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1]))
    .toSorted()
    .join('&')
}

// Prompts user to select a file
// returns a promise that resolves to the selected file(s)
// options: accept, multiple
export function selectFiles(options) {
  options = options || {}
  return new Promise(function(resolve, reject) {
    var input = document.createElement('input')
    input.setAttribute('style', 'display: none')
    input.setAttribute('type', 'file')
    if(options.accept) {
      input.setAttribute('accept', options.accept)
    }
    if(options.multiple) {
      input.setAttribute('multiple', '')
    }
    document.body.appendChild(input)

    input.addEventListener('change', function() {
      resolve(input.files)
      document.body.removeChild(input)
    })
    input.click()
  })
}

export function CSVToArray(strData, strDelimiter) {
  // Check to see if the delimiter is defined. If not,
  // then default to comma.
  strDelimiter = (strDelimiter || ',')
  // Create a regular expression to parse the CSV values.
  var objPattern = new RegExp(
    (
      // Delimiters.
      '(\\' + strDelimiter + '|\\r?\\n|\\r|^)' +

      // Quoted fields.
      // '(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|' +
      '(?:"([^"]*(?:""[^"]*)*)"|' +

      // Standard fields.
      // '([^\"\\' + strDelimiter + '\\r\\n]*))'
      '([^"\\' + strDelimiter + '\\r\\n]*))'
    ),
    'gi'
  )
  // Create an array to hold our data. Give the array
  // a default empty first row.
  var arrData = [[]]
  // Create an array to hold our individual pattern
  // matching groups.
  var arrMatches = objPattern.exec(strData)
  // Keep looping over the regular expression matches
  // until we can no longer find a match.
  while (arrMatches) {
    // Get the delimiter that was found.
    var strMatchedDelimiter = arrMatches[1]
    // Check to see if the given delimiter has a length
    // (is not the start of string) and if it matches
    // field delimiter. If id does not, then we know
    // that this delimiter is a row delimiter.
    if (strMatchedDelimiter.length && strMatchedDelimiter !== strDelimiter) {
      // Since we have reached a new row of data,
      // add an empty row to our data array.
      arrData.push([])
    }
    var strMatchedValue
    // Now that we have our delimiter out of the way,
    // let's check to see which kind of value we
    // captured (quoted or unquoted).
    if (arrMatches[ 2 ]) {
      // We found a quoted value. When we capture
      // this value, unescape any double quotes.
      strMatchedValue = arrMatches[ 2 ].replace(new RegExp('\'\'', 'g'), '\'')
    } else {
      // We found a non-quoted value.
      strMatchedValue = arrMatches[3]
    }
    // Now that we have our value string, let's add
    // it to the data array.
    arrData[ arrData.length - 1 ].push(strMatchedValue)
    arrMatches = objPattern.exec(strData)
  }
  // Return the parsed data.
  return arrData
}

export function pluck(array, key) {
  return array.map(function(x) { return x[key] })
}

export function min(array) {
  return array.reduce(function(a, b) {
    return (a === undefined || b < a) ? b : a
  }, undefined)
}

export function max(array) {
  return array.reduce(function(a, b) {
    return (a === undefined || b > a) ? b : a
  }, undefined)
}

export function uniq(array) {
  return [...new Set(array)]
}

export function pick(obj, keys) {
  return Object.fromEntries(keys.map(key => [key, obj[key]]))
}

export function humanizeStatus(str) {
  return {
    init: 'Not checked yet',
    checked_ok: 'Checked (OK)',
    checked_error: 'Checked (error)',
    checking: 'Checking',
    importing: 'Importing',
    imported: 'Imported (unapproved)',
    approved: 'Imported',
    import_error: 'Error during import'
  }[str]
}

export function formatDateTime(str) {
  if(!str) {
    return ''
  }
  let date = new Date(Date.parse(str))
  if(!date) {
    return ''
  }
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
}

export function debounce(fn, delay) {
  var timerId
  return function() {
    clearTimeout(timerId)
    var args = arguments
    var self = this
    timerId = setTimeout(function() {
      fn.apply(self, args)
    }, delay)
  }
}

export function readTextFile(mimeType, callback) {
  var input = document.createElement("input")
  input.type = "file"
  input.accept = mimeType
  input.addEventListener("change", function(evt) {
    var file = input.files[0]
    var reader = new FileReader()
    reader.readAsText(file)
    reader.onload = function() {
      callback(reader.result)
    }
  })
  document.body.append(input)
  input.click()
}

export function saveTextFile(text, mimeType, fileName) {
  var data = new Blob([text], { type: mimeType })
  var url = window.URL.createObjectURL(data)
  var link = document.createElement("a")
  link.href = url
  link.download = fileName
  document.body.append(link)
  link.click()
  window.URL.revokeObjectURL(url)
}

// Not currently used, but might be useful for Species IDs list
function parseCSV(input) {
  var p = 0
  var c = input[0]
  var quote = '"'
  var comma = ','
  var rows = []
  var row = []

  function endRow() {
    rows.push(row)
    row = []
  }

  function next() {
    if(eof()) { throw "Unexpected EOF" }
    c = input[++p]
  }

  function eof() {
    return p >= input.length
  }

  while(true) {
    var w = ''
    if(c === quote) {
      next()
      while(true) {
        if(c !== quote) {
          w += c; next()
        } else if(input[p + 1] === quote) {
          w += c; p++; next()
        } else {
          next(); break
        }
      }
    } else {
      w = ''
      while(!eof() && c !== comma && c !== '\n' && c !== '\r') {
        w += c; next()
      }
    }

    row.push(w)

    if(c === comma) {
      next()
    } else if(c === '\n') {
      next(); endRow()
    } else if(c === '\r') {
      next()
      if(c === '\n') { next() }
      endRow()
    } else if(eof()) {
      endRow(); break
    } else {
      throw "Unexpected char at index " + p + ": " + c
    }
  }
  return rows
}

export function extractSpeciesIDsFromCSV(csv) {
  return csv
        .split(/[\n\r]/)
        .flatMap(x => x.split(","))
        .map(x => x.trim())
        .filter(x => x.match(/^[pmu_]+[0-9]+[a-z]?$/))
}

export function generateSpeciesCSV(species) {
  function sanitise(x) {
    return x.replace(/[,\n\"]/g, ' ')
  }

  var header = "TaxonCommonName,TaxonScientificName,TaxonID\n"

  var csv = header + species.map(sp => {
    return sanitise(sp.common_name || "") + "," + sanitise(sp.scientific_name || "") + "," + (sp.id)
  }).join("\n")

  return csv
}

export function deepClone(a) {
  if(typeof a != "object" || a === null) {
    return a
  } else if(Array.isArray(a)) {
    return a.map(x => deepClone(x))
  } else {
    return Object.fromEntries(Object.entries(a).map(e => [e[0], deepClone(e[1])]))
  }
}

export function deepEquals(a, b) {
  if(Object.is(a, b)) {
    return true
  } else if(Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((ai, i) => deepEquals(ai, b[i]))
  } else if(typeof a === "object" && typeof b === "object") {
    let ak = Object.keys(a), bk = Object.keys(b)
    return ak.length === bk.length && ak.every(k => deepEquals(a[k], b[k]))
  } else {
    return false;
  }
}

export function generateCitation(authors, details, provider) {
  let year = new Date().getFullYear();
  function fix(str) {
    return (str || "").trim().replace(/\.$/, '')
  }

  authors = fix(authors) || "<Author(s)>";
  details = fix(details) || "<Data Details>"
  provider = fix(provider) || "<Data Provider>"

  return `${authors} (${year}). ${details}. ${provider}. Aggregated for the Australian Threatened Species Index, an output of the NESP Threatened Species Recovery Hub and operated by the Terrestrial Ecosystem Research Network, The University of Queensland.`
}

export function handleLinkClick(evt, url, router) {
    let openInNewTab =
      (evt.metaKey && /Mac/.test(navigator.platform)) ||
      (evt.ctrlKey && !/Mac/.test(navigator.platform)) ||
      evt.button == 1

    if(openInNewTab) {
      let routeData = router.resolve(url)
      window.open(routeData.href, '_blank')
    } else {
      router.push(url)
    }
}

// Unlike debounce(), fn is called immediately at first
export function throttle(fn, delay) {
  let state = 0
  function throttleWrapper() {
    if(state == 0) {
      fn.apply(this, [...arguments])
      state = 1
      setTimeout(() => {
        let oldState = state
        state = 0
        if(oldState == 2) {
          throttleWrapper.apply(this, [...arguments])
        }
      }, delay)
    } else {
      state = 2
    }
  }
  return throttleWrapper
}

export function searchStringToRegex(search) {
  //https://stackoverflow.com/a/3561711/165783
  return new RegExp(search.replace(/[/\-\\^$*+?.()|[\]{}]/g, '\\$&'), "gi")
}


// Converts a string to an array of string pairs, where each pair
// consists of a non-matching part followed by a matching part.
// E.g. matchParts("Tomato Mate", /mat/gi) =>
// [['to', 'mat'], ['o ', 'Mat'], ['e', '']]
export function matchParts(str, regex) {
  var i = 0
  var result = []
  for(let match of str.matchAll(regex)) {
    let j = match.index + match[0].length
    result.push([
      str.substring(i, match.index),
      str.substring(match.index, j)
    ])
    i = j
  }
  result.push([str.substr(i, str.length), ""])
  return result
}
