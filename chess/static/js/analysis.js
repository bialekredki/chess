class AnalysisState {

    constructor(data) {
        console.log(data.classification);
        this.classification = data.classification;
        this.colour = data.colour;
        this.eval = data.eval;
        this.fen = data.fen;
        this.tiles = data.tiles;
        this.move = data.move;
    }
}

class Analysis {

    constructor(data) {
        this.states = new Array();
        this.DEPTH_INCREMENT = 1;
        this.DEPTH_MAX = 20;
        this.locked = false;
        this.timeout = null;
        data['states'].forEach(function(value, index, number) {
            this.states.push(new AnalysisState(value));
        }, this)
        this.depth = data['depth'];
    }

    clearTimeout() {
        if (this.timeout != null) {
            clearTimeout(this.timeout.tid);
            this.timeout = null;
        }
    }

    timeoutSID() {
        if (this.timeout != null) return this.timeout.sid;
        return null;
    }

    timeoutTID() {
        if (this.timeout != null) return this.timeout.tid;
        return null;
    }

    getState(i) {
        return this.states[i];
    }

    getStateMove(i) {
        return this.states[i].move
    }

    getStateColour(i) {
        return this.states[i].colour;
    }

    getStateEval(i) {
        return this.states[i].eval;
    }

    getStateEvalDepth(i) {
        return this.states[i].eval.depth;
    }

    getStateEvalDepthIncremented(i) {
        let depth = this.getStateEvalDepth(i) + this.DEPTH_INCREMENT;
        if (depth > this.DEPTH_MAX) return null;
        return depth;
    }

    getStateFen(i) {
        return this.states[i].fen;
    }

    getStateTiles(i) {
        return this.states[i].tiles;
    }

    getStateClassification(i) {
        return this.states[i].classification;
    }

    updateEval(i, data) {
        console.log(data);
        this.states[i].eval = data;
        this.states[i].eval.depth = Number(data.depth);
    }

    classificationToTHMLSpan(i) {
        let classification = this.getStateClassification(i).name;
        let className = 'classification ' + classification.toLowerCase();
        return `<span class='${className}'>${classification}</span>`
    }

}