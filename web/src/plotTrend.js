
import {
  Chart,
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
} from 'chart.js';

Chart.register(
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
)

export function plotTrend(data, dom) {
  let series = data.split('\n')
      .slice(1) // Ignore first line
      .filter(line => line.trim().length > 0 && !/NA/.test(line)) // Ignore empty or NA lines
      .map(line => line.split(' '))

  let labels = series.map(x => parseInt(x[0].replace(/"/g, '')))
  let index = series.map(x => parseFloat(x[1]))
  let lowerCI = series.map(x => parseFloat(x[2]))
  let upperCI = series.map(x => parseFloat(x[3]))

  let hasCI = index.map((x, i) => lowerCI[i] !== upperCI[i])
  let solidIndex = index.map((x, i) => hasCI[i] || hasCI[i - 1] || hasCI[i + 1] ? x : undefined)
  let dashedIndex = index.map((x, i) => hasCI[i] ? undefined : x)

  let minYear = labels[0]

  let plotData = {
    labels: labels,
    datasets: [{
      label: 'TSX',
      borderColor: '#36699e',
      backgroundColor: 'black',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      data: solidIndex
    }, {
      label: 'TSX',
      display: false,
      borderColor: '#36699e',
      backgroundColor: 'black',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      borderDash: [5, 5],
      data: dashedIndex
    }, {
      label: 'Confidence Interval (low)',
      backgroundColor: 'rgba(230,230,230,0.5)',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      borderColor: '#0000',
      borderWidth: 1,
      data: lowerCI
    }, {
      label: 'Confidence Interval (high)',
      // backgroundColor: '#eee',
      backgroundColor: 'rgba(230,230,230,0.5)',
      fill: 2, // Fill between this dataset and dataset[1], i.e. between low & hi CI
      pointRadius: 0,
      lineTension: 0,
      borderColor: '#0000',
      borderWidth: 0,
      data: upperCI
    }]
  }

  let plot = new Chart(dom.getContext('2d'), {
    type: 'line',
    data: plotData,
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      maintainAspectRatio: true,
      scales: {
        yAxis: {
          display: true,
          position: 'left',
          grid: {
            display: true
          },
          ticks: {
            callback: function(label, index, labels) {
              // Show appropriate number of decimal places
              let delta = (labels.length > 1) ? Math.abs(labels[1].value - labels[0].value) : 0
              let decimalPlaces = (delta > 0) ? Math.min(5, Math.max(1, -Math.floor(Math.log10(delta)))) : 1
              return (+label).toFixed(decimalPlaces)
            }
          },
          title: {
            display: true,
            text: 'Index (' + minYear + ' = 1)'
          }
        },
        xAxis: {
          title: {
            display: true,
            text: 'Year'
          }
        }
      }
    }
  })
}
