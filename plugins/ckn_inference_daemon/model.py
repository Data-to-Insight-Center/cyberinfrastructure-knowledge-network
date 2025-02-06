import logging
import os
from models.model_store import ModelStore
logger = logging.getLogger(__name__)

# Read the model type from configuration (defaulting to imagenet)
MODEL_TYPE = os.getenv("MODEL_TYPE", "vision_transformer").lower()

# Instantiate the model store (which handles model retrieval and loading).
model_store = ModelStore()

def _get_plugin_instance():
    """
    Returns the appropriate model plugin instance based on the MODEL_TYPE configuration.
    """
    if MODEL_TYPE == "imagenet":
        from models.image_net_model import ImageNetModel
        return ImageNetModel(
            model_store.model,
            getattr(model_store, "feature_extractor", None)
        )
    elif MODEL_TYPE == "vision_transformer":
        from models.hf_transformer_vision_llm import HFTransformerVisionLLM
        return HFTransformerVisionLLM(
            model_store.model
        )
    # elif MODEL_TYPE == "sound":
    #     from sound_model import SoundModel
    #     return SoundModel(model_store.model, os.getenv("SOUND_CLASSES_PATH", "sound_classes.txt"))
    else:
        raise ValueError(f"Unsupported MODEL_TYPE: {MODEL_TYPE}")

# Initialize the current model plugin based on configuration.
current_model = _get_plugin_instance()

def load_model(model_name):
    """
    Loads a new model by name. This function is used to perform the initial load.
    """
    model_store.change_model(model_name)
    global current_model
    current_model = _get_plugin_instance()

def change_model(model_name):
    """
    Changes the current model to the one specified by model_name.
    This function updates the model store and resets the pluggable model interface.
    """
    load_model(model_name)

def pre_process(filename):
    """
    Pre-processes the input file using the current model's pre_process method.
    """
    return current_model.pre_process(filename)

def predict(input):
    """
    Runs the current model's predict method on the pre-processed input.
    """
    return current_model.predict(input)
