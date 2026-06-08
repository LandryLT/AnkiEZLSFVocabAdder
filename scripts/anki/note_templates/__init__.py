from importlib.resources import files

templates = files("scripts").joinpath("anki", "note_templates")

back_template = templates.joinpath("back.html").read_text(encoding="utf-8")
resti_front_template = templates.joinpath("resti_front.html").read_text(encoding="utf-8")
expre_front_template = templates.joinpath("expre_front.html").read_text(encoding="utf-8")
styles = templates.joinpath("styles.css").read_text(encoding="utf-8")

