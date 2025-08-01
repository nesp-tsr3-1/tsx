<template>
  <div class="section">
    <div class="columns">
      <div class="column is-8 is-offset-2">
        <user-nav></user-nav>

        <h2 class="title">Documents</h2>

        <div class="tabs is-boxed">
          <ul>
            <li>
              <router-link
                :to="{ name: 'DataAgreementHome' }">
                Data Sharing Agreements
                <span v-if="stats">&nbsp;({{stats.data_agreement_count}})</span>
              </router-link>
            </li>
            <li class="is-active">
              <router-link
                :to="{ name: 'AcknowledgementLetterHome' }">
                Acknowledgement Letters
                <span v-if="stats">&nbsp;({{stats.acknowledgement_letter_count}})</span>
              </router-link>
            </li>
          </ul>
        </div>

        <hr>

        <div v-if="status == 'loading'">
            <p>
            Loading…
          </p>
        </div>

        <div v-if="status == 'error'">
          <p>
            Failed to load acknowledgement letters.
          </p>
        </div>

        <div v-if="status == 'loaded'">
          <div v-if="letters.length == 0" class="columns">
            <p class="column content">No data acknowledgement letters to show.</p>
          </div>

          <div v-if="letters.length > 0" class="columns">
            <p class="column title is-6">Showing {{filteredLetters.length}} / {{letters.length}} letters</p>
            <input class="column input" type="text" placeholder="Search acknowledgement letters" v-model="searchText">
          </div>

          <table class="table is-fullwidth is-striped is-hoverable" v-if="filteredLetters.length > 0">
            <thead>
              <tr>
                <th @click="sortBy('filenames')">Filename(s) {{sortIcon('filenames')}}</th>
                <th @click="sortBy('year')">Year {{sortIcon('year')}}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="letter in sortedLetters">
                <td :title="letter.filenames">
                  <div v-for="file in letter.files">
                    <a :href="fileURL(file)">
                      <template v-for="[nonMatch, match] in file.filenameParts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </a>
                  </div>
                  <div v-if="letter.files.length == 0">
                    (No files)
                  </div>

                  <div style="display: flex;gap: 0.5em;">
                    <span v-for="parts in letter.custodianParts" class="tag is-info is-light">
                      <template v-for="[nonMatch, match] in parts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </span>
                  </div>
                </td>
                <td>{{letter.year}}</td>
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
import { searchStringToRegex, matchParts, debounce } from '../util.js'

export default {
  name: 'AcknowledgementLetterHome',
  data () {
    return {
      status: 'loading',
      letters: [],
      sort: {
        key: 'year',
        asc: false
      },
      searchText: '',
      debouncedSearchText: '',
      currentUser: null,
      stats: null
    }
  },
  computed: {
    filteredLetters() {
      let search = this.debouncedSearchText

      if(search) {

        let searchRegex = searchStringToRegex(search)

        function filterLetter(letter) {
          return letter.files.some(x => x.filename.match(searchRegex)) ||
            letter.custodians?.some(x => x.match(searchRegex))
        }

        let matchingLetters = this.letters.filter(filterLetter)
        for(let letter of matchingLetters) {
          for(let file of letter.files) {
            file.filenameParts = matchParts(file.filename, searchRegex)
          }
          letter.custodianParts = (letter.custodians || [])
            .map(custodian => matchParts(custodian, searchRegex))
            .filter(parts => parts.length > 1)
        }
        return matchingLetters
      } else {
        return this.letters.map(letter => ({
          ...letter,
          files: letter.files.map(file => ({
            ...file,
            filenameParts: [[file.filename, ""]]
          })),
          custodianParts: []
        }))
      }
    },
    sortedLetters() {
      let key = this.sort.key

      function compare(a, b) {
        if(typeof a == "number" && typeof b == "number") {
          return a - b
        } else {
          return (a ?? '').localeCompare(b ?? '')
        }
      }

      let result = this.filteredLetters.slice().sort((a, b) => compare(a[key], b[key]))
      if(!this.sort.asc) {
        result.reverse()
      }
      return result
    },
    isAdmin() {
      return this.currentUser?.roles?.includes('Administrator') === true
    }
  },
  methods: {
    refresh() {
      this.status = 'loading'

      Promise.all([
        api.acknowledgementLetters(),
        api.documentStats()
      ]).then(([letters, stats]) => {
        this.letters = letters
        this.letters.forEach(letter => {
          if(letter.files.length > 0) {
            letter.filenames = letter.files.map(f => f.filename).join(', ')
          } else {
            letter.filenames = '(No files)'
          }
        })
        this.stats = stats
        this.status = 'loaded'
      }).catch(error => {
        console.log("Failed to load acknowledgement letters")
        console.log(error)
        this.status = 'error'
      })
    },
    fileURL(file) {
      return api.uploadURL(file.upload_uuid)
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
    }
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

</style>
