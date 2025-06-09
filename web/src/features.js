
function setFeatureFlag(str, enabled) {
	localStorage["feat_" + str] = enabled ? "true" : "false"
}

function getFeatureFlag(str) {
	return localStorage["feat_" + str] === "true"
}

class Features {
	get documents() {
		return getFeatureFlag("documents")
	}

	set documents(x) {
		setFeatureFlag("documents", x)
	}
}

let instance = new Features()

export default instance
