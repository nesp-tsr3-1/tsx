
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
} from 'chart.js'

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

export function plotConsistency(data, dom) {
  let plotData = generateConsistencyPlotData(data)
  let plot = new Chart(dom.getContext('2d'), {
    type: 'scatter',
    data: plotData,
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      elements: {
        point: {
          radius: 2
        }
      },
      tooltips: {
        mode: 'point'
      },
      plugins: {
        tooltip: {
          callbacks: {
            label(context) {
              return context.label + ' (' + context.parsed.x + ')'
            }
          }
        },
        legend: {
          display: false
        }
      },
      scales: {
        yAxis: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Sites (time series)'
          },
          ticks: {
            callback: function(label, index, labels) {
              return Number.isInteger(label) ? label.toString() : ''
            }
          }
        },
        xAxis: {
          type: 'linear',
          ticks: {
            callback: function(label, index, labels) {
              return Number.isInteger(label) ? label.toString() : ''
            }
          },
          title: {
            display: true,
            text: 'Year'
          }
        }
      }
    }
  })

  return plot
}

export function generateConsistencyPlotData(data) {
  let seriesData = data.flatMap((timeSeries, timeSeriesIndex) =>
    timeSeries.map(([year, count]) => ({
      x: year,
      y: timeSeriesIndex + 1
    }))
  )

  return {
    datasets: [{
      backgroundColor: '#333',
      borderColor: '#333',
      borderWidth: 2,
      data: seriesData
    }]
  }
}
