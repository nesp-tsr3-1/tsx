import * as util from './util'

// export const ROOT_URL = 'https://tsx.org.au/tsxapi'

export const ROOT_URL = 'http://localhost:5000'

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

export function showImport(id) {
  return post("/imports/" + id + "/show")
}

export function hideImport(id) {
  return post("/imports/" + id + "/hide")
}

export function dataSources(criteria) {
  return get('/data_sources', criteria)
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

export function dataSourceSiteSummary(id) {
  return get('/data_sources/' + id + '/site_summary')
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

export function monitoringProgram(program_id) {
  return get('/monitoring_programs/' + program_id)
}

export function createMonitoringProgram(program) {
  return post('/monitoring_programs', program)
}

export function updateMonitoringProgram(program) {
  return put('/monitoring_programs/' + program.id, program)
}

export function deleteMonitoringProgram(id) {
  return del('/monitoring_programs/' + id)
}

export function removeSourceFromMonitoringProgram(program_id, source_id) {
  return del('/monitoring_programs/' + program_id + '/sources/' + source_id)
}

export function removeManagerFromMonitoringProgram(program_id, user_id) {
  return del('/monitoring_programs/' + program_id + '/managers/' + user_id)
}

export function addManagerToMonitoringProgram(programId, email) {
  return post('/monitoring_programs/' + programId + '/managers', { email })
}

export function programManagers(program_id) {
  return get('/programs/' + program_id + '/managers')
}

export function programsManagedBy(user_id) {
  return get('/users/' + user_id + '/programs')
}

export function updateProgramsManagedBy(user_id, program_ids) {
  return put('/users/' + user_id + '/programs', program_ids)
}

// -- visualisation urls

export function spatialIntensity(params) {
  return get('/results/spatial', params)
}

export function diagnosticPlots(params) {
  return get('/results/plots', params)
}

export function visualisationParameters(params) {
  return get('/results/params', params)
}

export function trend(params) {
  return get('/results/trends', params)
}

export function trendURL(params) {
  return ROOT_URL + '/results/trends?format=raw&' + util.encodeParams(params)
}

export function summaryURL(params) {
  return ROOT_URL + '/results/stats.html?' + util.encodeParams(params)
}

export function timeSeriesURL(params) {
  return ROOT_URL + '/results/time_series?' + util.encodeParams(params)
}

// -- end visualisation urls

export function createUser(user) {
  return post('/users', user)
}

export function updateUser(userId, userData) {
  return put('/users/' + userId, userData);
}

export function dataSourceProcessedData(id) {
  return get('/data_sources/' + id + '/processed_data')
}

export function dataSourceProcessedDataItemURL(data_source_id, item_id) {
  return ROOT_URL + '/data_sources/' + data_source_id + '/processed_data/' + item_id
}

export function dataSubsetDownloadURL(downloadType, params) {
  return ROOT_URL + '/subset/' + downloadType + '?' + util.encodeParams(params)
}

export function dataSubsetStats(params) {
  return get('/subset/stats', params)
}

export function dataSubsetIntensityMap(params) {
  return get('/subset/intensity_map', params)
}

export function dataSubsetSites(params) {
  return get('/subset/sites', params)
}

export function dataSubsetSpecies(params) {
  return get('/subset/species', params)
}

export function dataSubsetConsistencyPlot(params) {
  return get('/subset/monitoring_consistency', params)
}

export function dataSubsetGenerateTrend(params) {
  return post('/subset/trend', params)
}

export function dataSubsetTrendStatus(id) {
  return get('/subset/trend/' + id + '/status')
}

export function dataSubsetTrend(id) {
  return get('/subset/trend/' + id)
}

export function dataSubsetTrendDiagnostics(id) {
  return get('/subset/trend/' + id + '/diagnostics')
}

export function dataSubsetTrendDownloadURL(id) {
  return ROOT_URL + '/subset/trend/' + id + '?format=csv'
}

export function dataSubsetFilenameComponent(params) {
  return get('/subset/filename', params)
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

export function region() {
  return get('/region')
}

export function searchtype() {
  return get('/searchtype')
}

export function species(args) {
  return get('/species', args)
}

export function speciesForIDs(ids) {
  return get('/species', { q: 'ids', ids: ids.join(',') })
}

export function source() {
  return get('/source')
}

export function status() {
  return get('/status')
}

export function dataAgreementStatusOptions() {
  return get('/data_agreement_status')
}

export function deleteImport(id) {
  return del('/imports/' + id)
}

export function intensiveManagementGroup(id) {
  return get('/intensive_management_group')
}

export function taxonomicGroups() {
  return get('/taxonomic_group')
}

export function taxonDatasets() {
  return get('/custodian_feedback/taxon_datasets')
}

export function taxonDataset(id) {
  return get('/custodian_feedback/taxon_datasets/' + id)
}

export function custodianFeedbackForm(id) {
  return get('/custodian_feedback/forms/' + id)
}

export function custodianFeedbackFormPDFURL(id) {
  return ROOT_URL + '/custodian_feedback/forms/' + id + '/pdf'
}

export function custodianFeedbackFormDownloadURL(id) {
  return ROOT_URL + '/custodian_feedback/forms/' + id + '/download'
}

export function custodianFeedbackFormCSVURL(id) {
  return ROOT_URL + '/custodian_feedback/forms/' + id + '/csv'
}

export function updateCustodianForm(id, data) {
  return put('/custodian_feedback/forms/' + id, data)
}

export function custodianFeedbackFormDefinition() {
  return get('/custodian_feedback/form_definition')
}

export function custodianFeedbackPreviousAnswers(id) {
  return get('/custodian_feedback/previous_answers', { form_id: id })
}

export function dataAgreements(params) {
  return get('/documents/data_agreements', params)
}

export function dataAgreement(id) {
  return get('/documents/data_agreements/' + id)
}

export function dataAgreementCSVURL(id) {
  return ROOT_URL + '/documents/data_agreements/' + id + '/csv'
}

export function createDataAgreement(data) {
  return post('/documents/data_agreements', data)
}

export function updateDataAgreement(id, data) {
  return put('/documents/data_agreements/' + id, data)
}

export function deleteDataAgreement(id) {
  return del('/documents/data_agreements/' + id)
}


export function acknowledgementLetters(params) {
  return get('/documents/acknowledgement_letters', params)
}

export function documentStats() {
  return get('/documents/stats')
}

export function upload(file, progressCallback) {
  // Flask seems to need files to be uploaded as multipart/form-data for some reason..
  var data = new FormData()
  data.append('file', file)

  // Must pass contentType = null for multipart/form-data
  return post('/uploads', data, null, progressCallback).then(function(result) {
    return {
      ...result,
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
  params = { ...params }

  var options = params._options || {}
  delete params._options

  if(Object.entries(params).length > 0) {
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

  Object.entries(options.headers || {}).forEach(([v, k]) => {
    xhr.setRequestHeader(k, v)
  })

  return xhrPromise(xhr).then(function(xhr) {
    var response = xhr.responseText
    try { response = JSON.parse(response) } catch(e) {}
    return response
  })
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
