from anki.storage import Collection
from anki.models import  NotetypeDict
from scripts.anki.note_templates import styles, back_template, expre_front_template, resti_front_template
import logging

class AnkiModelGen():
    logger = logging.getLogger(__name__)
    def __init__(self, col: Collection, model_name: str):
        self.col = col
        self.model_name = model_name

    def findModel(self) -> NotetypeDict:
        self.model = None
        models = self.col.models.all()
        for m in models:
            if m['name'] == self.model_name:
                self.logger.info("Found LSF model in Anki")
                self.model = self.col.models.get(m['id'])
                continue

        if not self.model:
            self.logger.info("LSF note model not found")
            self.model = self.genModel()
        else:
            self.updateModel()

        self.col.models.update(self.model)
        
        return self.model

    def updateModel(self):
        resti_template = self.model["tmpls"][0]
        expre_template = self.model["tmpls"][1]
        resti_template["qfmt"] = resti_front_template
        resti_template["afmt"] = back_template
        expre_template["qfmt"] = expre_front_template
        expre_template["afmt"] = back_template
        self.model["css"] = styles
        self.col.models.update_dict(self.model)
  

    def genModel(self) -> NotetypeDict:
        self.logger.info("Generating LSF note model")
        anki_models = self.col.models
        model = anki_models.new(self.model_name)
        anki_models.add_field(model, anki_models.new_field("Name"))
        anki_models.add_field(model, anki_models.new_field("Typology"))
        anki_models.add_field(model, anki_models.new_field("Definitions"))
        anki_models.add_field(model, anki_models.new_field("Word Signs"))
        anki_models.add_field(model, anki_models.new_field("Definition Signs"))
        anki_models.add_field(model, anki_models.new_field("Sign Writings"))
        
        restitution_template = anki_models.new_template("Restitution Card")
        expression_template = anki_models.new_template("Expression Card")
        
        restitution_template["qfmt"] = resti_front_template
        restitution_template["afmt"] = back_template
        expression_template["qfmt"] = expre_front_template
        expression_template["afmt"] = back_template
        model["css"] = styles

        anki_models.add_template(model, restitution_template)
        anki_models.add_template(model, expression_template)

        anki_models.add_dict(model)