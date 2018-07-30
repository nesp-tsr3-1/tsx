from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker(
    "TSXAPI",
    "tsx.api.tap",
    "TSX web-service",
    "tsxapi"
)
