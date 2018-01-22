import Promise from 'bluebird' // We can drop this when browser support is better
// import * as util from 'util'
import * as util from '@/util'
import _ from 'underscore'

// const ROOT_URL = 'http://192.168.168.4:5000'
// const ROOT_URL = 'http://localhost:5000'
export const NESP_URL = 'https://203.101.225.200'
export const ROOT_URL = NESP_URL + '/nespapi'

export function createImport(dataImport) {
  return post('/imports', dataImport)
}

export function updateImport(id, dataImport) {
  return put('/imports/' + id, dataImport)
}

export function dataImports() {
  return get('/imports')
}

export function dataImport(id) {
  return get('/imports/' + id)
}

export function dataImportLog(id) {
  return get('/imports/' + id + '/log')
}

export function lpidata(params) {
  return get('/lpi-data', params)
}

export function lpiDownloadURL(params) {
  return ROOT_URL + '/lpi-data?' + util.encodeParams(params)
}

export function lpiPlot(params) {
  return get('/lpi-data/plot', params)
}

// TODO: if files are in object stores, update this
export function lpiRunData(path, filetype) {
  var baseLPIRunURL = NESP_URL + '/lpi_runs/'
  var url = ''
  if(!_.isEmpty(path)) {
    url += encodeURI(path)
  } else { // default one
    url += encodeURI('statusauth-Max_')
  }
  console.log(url)
  var xhr = new XMLHttpRequest()
  xhr.open('GET', baseLPIRunURL + url)
  console.log(baseLPIRunURL + url)
  // Used for debugging (e.g. in exceptions)
  var params = {}
  var options = {}
  xhr._meta = {
    url: url,
    method: 'GET',
    params: params,
    options: options
  }
  xhr.responseType = ''
  xhr.withCredentials = true

  _.each(options.headers || {}, function(v, k) {
    xhr.setRequestHeader(k, v)
  })
  // var accessToken = util.store.get('accessToken');
  // if(accessToken) {
  //   xhr.setRequestHeader("Authorization", "Bearer " + accessToken);
  // }
  return xhrPromise(xhr).then(function(xhr) {
    var response = xhr.responseText
    if(filetype === 'json') {
      try { response = JSON.parse(response) } catch(e) {}
    }
    return response
  })
  .catch(function(e) {
    console.log('Error:' + e)
  })
}

export function region() {
  return get('/region')
}

export function searchtype() {
  return get('/searchtype')
}

export function species() {
  return get('/species')
}

export function source() {
  return get('/source')
}

export function status() {
  return get('/status')
}

export function deleteImport(id) {
  return del('/imports/' + id)
}

export function upload(file, progressCallback) {
  // Flask seems to need files to be uploaded as multipart/form-data for some reason..
  var data = new FormData()
  data.append('file', file)

  // Must pass contentType = null for multipart/form-data
  return post('/uploads', data, null, progressCallback).then(function(result) {
    return {
      uuid: result.uuid,
      url: ROOT_URL + '/uploads/' + result.uuid
    }
  })
}

export function uploadURL(uuid) {
  return ROOT_URL + '/uploads/' + uuid
}

function put(url, data, contentType, progressCallback) {
  return putOrPost('PUT', url, data, contentType, progressCallback)
}

function post(url, data, contentType, progressCallback) {
  return putOrPost('POST', url, data, contentType, progressCallback)
}

function putOrPost(method, url, data, contentType, progressCallback) {
  var xhr = new XMLHttpRequest()

  if(!contentType && !(data instanceof FormData)) {
    data = JSON.stringify(data)
    contentType = 'application/json'
  }

  xhr.open(method, ROOT_URL + url)
  if(contentType) {
    xhr.setRequestHeader('Content-Type', contentType)
  }
  // xhr.setRequestHeader('Content-Disposition', 'attachment; filename=' + JSON.stringify(file.name));

  if(progressCallback) {
    xhr.upload.addEventListener('progress', function(evt) {
      if(evt.lengthComputable) {
        progressCallback(evt.loaded / evt.total)
      } else {
        progressCallback(-evt.loaded)
      }
    })
  }

  return xhrPromise(xhr, data).then(function(xhr) {
    var response = xhr.responseText
    try { response = JSON.parse(response) } catch(e) {}
    return response
  })
}

function del(url) {
  var xhr = new XMLHttpRequest()
  xhr.open('DELETE', ROOT_URL + url)

  xhr._meta = {
    url: url,
    method: 'DELETE'
  }

  xhr.withCredentials = true

  return xhrPromise(xhr).then(function(xhr) {
    var response = xhr.responseText
    try { response = JSON.parse(response) } catch(e) {}
    return response
  })
}

function get(url, params) {
  params = params || {}

  var options = params._options || {}
  params = _.omit(params, '_options')

  if(!_.isEmpty(params)) {
    url += '?' + util.encodeParams(params)
  }

  var xhr = new XMLHttpRequest()
  xhr.open('GET', ROOT_URL + url)
  // console.log(ROOT_URL + url)
  // Used for debugging (e.g. in exceptions)
  xhr._meta = {
    url: url,
    method: 'GET',
    params: params,
    options: options
  }

  xhr.responseType = ''
  xhr.withCredentials = true

  _.each(options.headers || {}, function(v, k) {
    xhr.setRequestHeader(k, v)
  })

  // var accessToken = util.store.get('accessToken');
  // if(accessToken) {
  //   xhr.setRequestHeader("Authorization", "Bearer " + accessToken);
  // }

  return xhrPromise(xhr).then(function(xhr) {
    var response = xhr.responseText
    try { response = JSON.parse(response) } catch(e) {}
    return response
  })

  // .catch(function(e) {
  //   if(xhr.status == 401) {
  //     return refreshAccessToken().then(() => get(url, params));
  //   }
  // })
}

function xhrPromise(xhr, dataToSend) {
  return new Promise(function(resolve, reject) {
    xhr.addEventListener('error', function() { reject(XHRError(xhr)) })
    xhr.addEventListener('load', function(evt) {
      // Check for error
      if(xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr)
      } else {
        reject(XHRError(xhr))
      }
    })
    xhr.send(dataToSend)
  })
}

function XHRError(xhr) {
  var url = xhr._meta ? xhr._meta.url : '?'
  var error = new Error('XHR Error ' + xhr.status + ': ' + url)
  error.xhr = xhr
  return error
}
