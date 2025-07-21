<template>
  <div class="section">
    <div class="columns">
      <div class="column is-8 is-offset-2">
        <user-nav></user-nav>

        <h2 class="title">Documents</h2>

        <div class="tabs is-boxed">
          <ul>
            <li class="is-active"><a>Data Sharing Agreements <span v-if="stats">&nbsp;({{stats.data_agreement_count}})</span>
            </a></li>
            <li><a>Acknowledgement Letters (TODO)</a></li>
          </ul>
        </div>

        <div class="buttons">
          <button class="button is-primary" @click="downloadAgreementTemplate">Download Agreement Template</button>
          <button class="button is-primary" @click="createNewAgreement" v-if="isAdmin">Upload New Agreement</button>
        </div>

        <p class="content">If you would like to enter into a new data sharing agreement, please download the agreement template above, complete it, and send it to the TSX team at tsx@tern.org.au.</p>
        <div class="notification is-info is-light" v-if="awaitingSignatureBanner">
          {{awaitingSignatureBanner}}
        </div>

        <hr>

        <div v-if="status == 'loading'">
            <p>
            Loading…
          </p>
        </div>

        <div v-if="status == 'error'">
          <p>
            Failed to load data agreements.
          </p>
        </div>

        <div v-if="status == 'loaded'">
          <div v-if="agreements.length == 0" class="columns">
            <p class="column content">No data sharing agreements to show.</p>
          </div>

          <div v-if="agreements.length > 0" class="columns">
            <p class="column title is-6">Showing {{filteredAgreements.length}} / {{agreements.length}} agreements</p>
            <input class="column input" type="text" placeholder="Search agreements" v-model="searchText">
          </div>

          <table class="table is-fullwidth is-striped is-hoverable" v-if="filteredAgreements.length > 0">
            <thead>
              <tr>
                <th @click="sortBy('filenames')">Filename(s) {{sortIcon('filenames')}}</th>
                <th @click="sortBy('commencement_date')">Commencement Date {{sortIcon('commencement_date')}}</th>
                <th v-if="isAdmin">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="agreement in sortedAgreements">
                <td :title="agreement.filenames">
                  <div v-for="file in agreement.files">
                    <a :href="fileURL(file)">
                      <template v-for="[nonMatch, match] in file.filenameParts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </a>
                  </div>
                  <div v-if="agreement.files.length == 0">
                    (No files)
                  </div>

                  <div style="display: flex;gap: 0.5em;">
                    <span v-for="parts in agreement.custodianParts" class="tag is-info is-light">
                      <template v-for="[nonMatch, match] in parts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </span>
                    <span v-for="parts in agreement.sourceParts" class="tag is-success is-light">
                      <template v-for="[nonMatch, match] in parts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </span>
                  </div>
                  <span class="tag is-warning" v-if="agreement.is_draft">Draft</span>
                </td>
                <td>{{formatDate(agreement.commencement_date)}}</td>
                <td v-if="isAdmin">
                  <div class="buttons">
                    <button
                      v-if="!agreement.is_draft"
                      class="button is-small is-primary"
                      @click='() => edit(agreement)'>Edit</button>
                    <button
                      v-if="agreement.is_draft"
                      class="button is-small is-dark"
                      @click='() => edit(agreement)'>Edit draft</button>
                    <a class="button is-small" target="_blank" :href="downloadURL(agreement)" v-if="downloadURL(agreement)">Download (CSV)</a>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { formatDate, searchStringToRegex, matchParts, debounce } from '../util.js'

export default {
  name: 'DataAgreementHome',
  data () {
    return {
      status: 'loading',
      agreements: [],
      sort: {
        key: 'commencement_date',
        asc: false
      },
      searchText: '',
      debouncedSearchText: '',
      currentUser: null,
      stats: null
    }
  },
  computed: {
    filteredAgreements() {
      let search = this.debouncedSearchText

      if(search) {

        let searchRegex = searchStringToRegex(search)

        function filterAgreement(agreement) {
          return agreement.files.some(x => x.filename.match(searchRegex)) ||
            agreement.sources?.some(x => x.match(searchRegex)) ||
            agreement.custodians?.some(x => x.match(searchRegex))
        }

        let matchingAgreements = this.agreements.filter(filterAgreement)
        for(let agreement of matchingAgreements) {
          for(let file of agreement.files) {
            file.filenameParts = matchParts(file.filename, searchRegex)
          }
          agreement.custodianParts = (agreement.custodians || [])
            .map(custodian => matchParts(custodian, searchRegex))
            .filter(parts => parts.length > 1)
          agreement.sourceParts = (agreement.sources || [])
            .map(source => matchParts(source, searchRegex))
            .filter(parts => parts.length > 1)
        }
        return matchingAgreements
      } else {
        return this.agreements.map(agreement => ({
          ...agreement,
          files: agreement.files.map(file => ({
            ...file,
            filenameParts: [[file.filename, ""]]
          })),
          custodianParts: [],
          sourceParts: []
        }))
      }
    },
    sortedAgreements() {
      let key = this.sort.key
      let result = this.filteredAgreements.slice().sort((a, b) => (a[key] || '').localeCompare(b[key] || ''))
      if(!this.sort.asc) {
        result.reverse()
      }
      return result
    },
    isAdmin() {
      return this.currentUser?.roles?.includes('Administrator') === true
    },
    awaitingSignatureBanner() {
      if(this.status == 'loaded' && this.isAdmin) {
        if(this.stats?.pending_uq_count > 1) {
          return "Note: There are " + this.awaiting_uq_count + " data sharing agreements waiting to be signed by UQ."
        } else if(this.stats?.pending_uq_count == 1) {
          return "Note: There is one data sharing agreement waiting to be signed by UQ."
        }
      }
    }
  },
  methods: {
    refresh() {
      this.status = 'loading'

      Promise.all([
        api.dataAgreements({ include_draft: true }),
        api.documentStats()
      ]).then(([agreements, stats]) => {
        this.agreements = agreements
        this.agreements.forEach(agg => {
          if(agg.files.length > 0) {
            agg.filenames = agg.files.map(f => f.filename).join(', ')
          } else {
            agg.filenames = '(No files)'
          }
        })
        this.stats = stats
        this.status = 'loaded'
      }).catch(error => {
        console.log("Failed to load data agreements")
        console.log(error)
        this.status = 'error'
      })
    },
    fileURL(file) {
      return api.uploadURL(file.upload_uuid)
    },
    downloadURL(agreement) {
      return api.dataAgreementCSVURL(agreement.id)
    },
    downloadAgreementTemplate() {
      alert("Not yet implemented")
    },
    createNewAgreement() {
      this.$router.push('/documents/data_agreements/edit/new')
    },
    edit(agreement) {
      this.$router.push("/documents/data_agreements/edit/" + agreement.id)
    },
    sortIcon(key) {
      if(this.sort.key === key) {
        return this.sort.asc ? '▲' : '▼'
      } else {
        return ''
      }
    },
    sortBy(key) {
      if(this.sort.key === key) {
        this.sort.asc = !this.sort.asc
      } else {
        this.sort = {
          key: key,
          asc: true
        }
      }
    },
    formatDate
  },
  created () {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    api.currentUser().then(currentUser => {
      this.currentUser = currentUser
    })
    this.refresh()
  },
  watch: {
    searchText: debounce(function(searchText) {
      this.debouncedSearchText = searchText
    }, 500)
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.dataset-details {
  margin-top: 1.5em;
}
.dataset-details > .column {
  margin-top: -1.5em;
}
.dataset-details h4 {
  font-weight: bold;
}
.dataset-details > .column > div {
  margin-bottom: 1em;
}
</style>
