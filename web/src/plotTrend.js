
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

  let plotData = {
    labels: labels,
    datasets: [{
      label: 'TSX',
      borderColor: '#36699e',
      backgroundColor: 'black',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      data: index
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
      fill: 1, // Fill between this dataset and dataset[1], i.e. between low & hi CI
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
              // Force labels to always show one decimal place
              return (+label).toFixed(1)
            }
          },
          title: {
            display: true,
            text: 'Index (1980 = 1)'
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
