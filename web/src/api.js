import Promise from 'bluebird' // We can drop this when browser support is better
// import * as util from 'util'
import * as util from '@/util'
import _ from 'underscore'

const LPI_RUNS_URL = 'https://tsx.org.au/lpi_runs'
export const ROOT_URL = 'https://tsx.org.au/tsxapi'

export function isLoggedIn() {
  return get('/is_logged_in')
}

export function createImport(dataImport) {
  return post('/imports', dataImport)
}

export function updateImport(id, dataImport) {
  return put('/imports/' + id, dataImport)
}

export function approveImport(id) {
  return post('/imports/' + id + '/approve')
}

export function dataSources() {
  return get('/data_sources')
}

export function dataSource(id) {
  return get('/data_sources/' + id)
}

export function dataSourceImports(id) {
  return get('/data_sources/' + id + '/imports')
}

export function dataSourceNotes(id) {
  return get('/data_sources/' + id + '/notes')
}

export function createDataSourceNote(dataSourceId, notes) {
  return post('/data_sources/' + dataSourceId + '/notes', { notes })
}

export function updateDataSourceNote(dataSourceId, noteId, notes) {
  return put('/data_sources/' + dataSourceId + '/notes/' + noteId, { notes })
}

export function deleteDataSourceNote(dataSourceId, noteId) {
  return del('/data_sources/' + dataSourceId + '/notes/' + noteId)
}

export function dataSourceCustodians(id) {
  return get('/data_sources/' + id + '/custodians')
}

export function addDataSourceCustodian(dataSourceId, email) {
  return post('/data_sources/' + dataSourceId + '/custodians', { email })
}

export function deleteDataSourceCustodian(dataSourceId, userId) {
  return del('/data_sources/' + dataSourceId + '/custodians/' + userId)
}

export function createDataSource(source) {
  return post('/data_sources', source)
}

export function updateDataSource(source) {
  return put('/data_sources/' + source.id, source)
}

export function deleteDataSource(id) {
  return del('/data_sources/' + id)
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

export function dataImportLogUrl(id) {
  return ROOT_URL + '/imports/' + id + '/log'
}

export function monitoringPrograms() {
  return get('/monitoring_program')
}

export function lpidata(params) {
  return get('/lpi-data', params)
}

export function lpiDownloadURL(params) {
  return ROOT_URL + '/lpi-data?' + util.encodeParams(params)
}

export function lpiSummaryURL(params) {
  return ROOT_URL + '/lpi-data/stats.html?' + util.encodeParams(params)
}

export function lpiPlot(params) {
  return get('/lpi-data/plot', params)
}

export function intensityPlot(params) {
  return get('/lpi-data/intensity', params)
}

export function createUser(user) {
  return post('/users', user)
}

export function login(email, password) {
  return post('/login', { email, password })
}

export function logout() {
  return post('/logout')
}

export function refreshCurrentUser() {
  currentUser.cached = undefined
}

export function currentUser() {
  if(!currentUser.cached) {
    currentUser.cached = get('/users/me')
  }
  return currentUser.cached
}

export function users() {
  return get('/users')
}

export function updateUserRole(userId, role) {
  return put('/users/' + userId + '/role', { role })
}

export function requestPasswordReset(email) {
  return post('/reset_password', { email })
}

export function resetPassword(code, password) {
  return post('/reset_password', { code, password })
}

// TODO: if files are in object stores, update this
export function lpiRunData(filterString, year) {
  if(_.isEmpty(filterString)) {
    filterString = 'statusauth-Max_'
  }

  // URI Encode everything except spaces and pluses because that's how the files are named on the server
  // filterString = filterString.split(' ').map(encodeURIComponent).join(' ')

  var url = encodeURI(LPI_RUNS_URL + '/' + filterString + '/nesp_' + year + '_infile_Results.txt')

  console.log(url)

  var xhr = new XMLHttpRequest()
  xhr.open('GET', url)

  // Used for debugging (e.g. in exceptions)
  xhr._meta = {
    url: url,
    method: 'GET'
  }
  xhr.responseType = ''
  xhr.withCredentials = true

  return xhrPromise(xhr).then(function(xhr) {
    return xhr.responseText
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

  if(data !== undefined) {
    if(!contentType && !(data instanceof FormData)) {
      data = JSON.stringify(data)
      contentType = 'application/json'
    }
  }

  xhr.open(method, ROOT_URL + url)
  xhr._meta = {
    url: url,
    method: method,
    data: data
  }

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

  xhr.withCredentials = true

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
  var url = xhr._meta ? xhr._meta.url : '(unknown URL)'
  var error = new Error('XHR Error ' + xhr.status + ': ' + url)
  error.xhr = xhr
  try {
    if(xhr.getResponseHeader('Content-Type') === 'application/json') {
      error.json = JSON.parse(xhr.responseText)
      console.log(error.json)
    }
  } catch(e) {
    console.log(e)
    console.log('Failed to parse JSON error response: ' + xhr.responseText)
  }
  return error
}
