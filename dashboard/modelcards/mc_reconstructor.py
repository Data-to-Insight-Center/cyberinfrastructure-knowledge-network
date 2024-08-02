import json
class MCReconstructor:
    """
    Re-constructs the model card from the Knowledge Graph
    """

    def __init__(self, graph):
        self.graph = graph

    def reconstruct(self, model_card_id):
        metadata = {
            "mc_id": model_card_id,
            "ai_model_id": str(model_card_id + "-model"),
            "xai_id": str(model_card_id + "-xai"),
            "bias_id": str(model_card_id + "-bias"),
        }

        # retrieve the base model card
        mc_query = '''
            MATCH (mc:ModelCard {external_id: $mc_id})
            RETURN mc
            '''
        base_mc = self.get_result_dict(mc_query, "mc", metadata)

        # retrieve the ai_model information
        ai_model_query = '''
            MATCH (ai:Model {model_id: $ai_model_id})
            RETURN ai
            '''
        ai_model = self.get_result_dict(ai_model_query, "ai", metadata)
        base_mc["ai_model"] = ai_model

        # retrieve bias information if any
        bias_query = '''
            MATCH (ba:BiasAnalysis {external_id: $bias_id})
            RETURN ba
            '''
        bias_analysis = self.get_result_dict(bias_query, "ba", metadata)
        if bias_analysis is not None:
            base_mc["bias_analysis"] = bias_analysis

        # retrieve explainability information if any
        xai_query = '''
            MATCH (xai:ExplainabilityAnalysis {external_id: $xai_id})
            RETURN xai
            '''
        xai_analysis = self.get_result_dict(xai_query, "xai", metadata)
        if xai_analysis is not None:
            base_mc["xai_analysis"] = bias_analysis

        return json.dumps(base_mc, indent=4)

    def get_result_dict(self, query, type, metadata):
        response = self.graph.get_result_query(query, metadata)
        node = response[type]

        result_dict = {}
        if node is not None:
            for key in node.keys():
                if key == 'embedding' or key == 'external_id' or key == 'model_id':
                    continue
                result_dict[key] = node[key]
        else:
            return None
        return result_dict