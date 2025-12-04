
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

export function formatDate(str) {
  if(!str) {
    return ''
  }
  let date = new Date(Date.parse(str))
  if(!date) {
    return ''
  }
  return date.toLocaleDateString(undefined, { timeZone: "UTC"})
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
export function parseCSV(input) {
  var p = 0
  var c = input[0]
  var quote = '"'
  var comma = ','
  var rows = []
  var row = []
  var lines = 1
  var lineStart = 0

  function endRow() {
    rows.push(row)
    row = []
  }

  function next() {
    if(eof()) { throw "Unexpected EOF" }
    c = input[++p]
    if(c === '\n') {
      lines++
      lineStart = p
    }
  }

  function eof() {
    return p >= input.length
  }

  if(eof()) {
    return []
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
        if(c === quote) {
          throw new Error("Unexpected double-quote (line: " + lines + ", char: " + (p - lineStart + 1) + ")")
        }
        w += c; next()
      }
    }

    row.push(w)

    if(c === comma) {
      next()
    } else if(c === '\n') {
      next(); endRow()
      if(eof()) { break }
    } else if(c === '\r') {
      next()
      if(c === '\n') { next() }
      endRow()
      if(eof()) { break }
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

export function deepEquals(a, b) {
  if(Object.is(a, b)) {
    return true
  } else if(Array.isArray(a) != Array.isArray(b)) {
    return false
  } else if(Array.isArray(a)) {
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
  let pendingArguments
  function throttleWrapper() {
    if(state == 0) {
      fn.apply(this, [...arguments])
      state = 1
      setTimeout(() => {
        let oldState = state
        state = 0
        if(oldState == 2) {
          throttleWrapper.apply(this, pendingArguments)
        }
      }, delay)
    } else {
      state = 2
      pendingArguments = [...arguments]
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

export function capitalise(str) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/*
Sets up automatic highlighting of a set of intra-page navigation links as the
user scrolls.
This function takes a dom element and searches for all link elements that are
descendants of that element. Only intra-page links are processed.
It then sets up a page scroll listener which adds a 'current' class to the
link element that the user is currently viewing.

Returns an object with a dispose() method which cleans up any resources.
*/
export function setupPageNavigationHighlighting(menuDom) {
  function updateMenu() {
    let sections = Array.from(menuDom.querySelectorAll("a"))
      .map(a => ({
        link: a,
        target: document.querySelector(a.getAttribute("href"))
      }))
      .filter(s => s.target)

    let currentSection = sections[0]

    for(let section of sections.slice(1)) {
      if(section.target.getBoundingClientRect().top > 50) { // window.innerHeight / 2) {
        break
      }
      currentSection = section
    }

    for(let section of sections) {
      section.link.classList.toggle('current', section === currentSection)
    }
  }

  let handler = throttle(updateMenu, 250)
  document.addEventListener("scroll", handler)
  setTimeout(updateMenu, 250);

  return {
    dispose() {
      document.removeEventListener("scroll", handler)
    }
  }
}
