import _ from 'underscore'

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
  return _.chain(params)
    .pairs()
    .map(function(p) {
      return encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1])
    })
    .sort()
    .value()
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
