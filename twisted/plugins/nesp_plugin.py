from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker(
    "NespRESTfulAPI",
    "nesp.api.tap",
    "NESP RESTful web-service",
    "nesprestapi"
)
