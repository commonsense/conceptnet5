# Globals
# =======
# Configuration of Unix programs
M4 = m4
INKSCAPE = inkscape

# Configuration of input filenames
CNET_DIAGRAMS = img/diagram_1.png img/diagram_2.png img/diagram_3.png \
				img/diagram_4.png img/diagram_5.png img/diagram_6.png \
				img/diagram_7.png

# Automatic diagram rendering
# ===========================
# Generate 7 versions of the ConceptNet diagram, with different layers
# visible.
#
# We've edited "img/diagram.svg" so that the layers have tags such as
# TEMPLATESTYLE="display: STEP1". We use m4 as a substitution engine,
# which turns these into the normal declarations of whether a layer
# is visible or not, such as style="display: inline".
VARS_STEP1 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=none   -DSTEP3A=none   -DSTEP4=none   -DSTEP4A=none   -DSTEP5=none   -DSTEP5A=none   -DSTEP6=none   -DSTEP7=none
VARS_STEP2 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=inline -DSTEP3A=none   -DSTEP4=none   -DSTEP4A=none   -DSTEP5=none   -DSTEP5A=none   -DSTEP6=none   -DSTEP7=none
VARS_STEP3 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=inline -DSTEP3A=inline -DSTEP4=none   -DSTEP4A=none   -DSTEP5=none   -DSTEP5A=none   -DSTEP6=none   -DSTEP7=none
VARS_STEP4 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=inline -DSTEP3A=inline -DSTEP4=inline -DSTEP4A=inline -DSTEP5=none   -DSTEP5A=none   -DSTEP6=none   -DSTEP7=none
VARS_STEP5 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=inline -DSTEP3A=inline -DSTEP4=inline -DSTEP4A=inline -DSTEP5=inline -DSTEP5A=inline -DSTEP6=none   -DSTEP7=none
VARS_STEP6 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=inline -DSTEP3A=inline -DSTEP4=inline -DSTEP4A=inline -DSTEP5=inline -DSTEP5A=inline -DSTEP6=inline -DSTEP7=none
VARS_STEP7 = -DTEMPLATESTYLE=style -DSTEP1=inline -DSTEP2A=none   -DSTEP3A=none   -DSTEP4=inline -DSTEP4A=none   -DSTEP5=inline -DSTEP5A=none   -DSTEP6=inline -DSTEP7=inline

diagrams: $(CNET_DIAGRAMS)

img/build/diagram_1.svg: img/diagram.svg
	$(M4) $(VARS_STEP1) $< > $@
img/build/diagram_2.svg: img/diagram.svg
	$(M4) $(VARS_STEP2) $< > $@
img/build/diagram_3.svg: img/diagram.svg
	$(M4) $(VARS_STEP3) $< > $@
img/build/diagram_4.svg: img/diagram.svg
	$(M4) $(VARS_STEP4) $< > $@
img/build/diagram_5.svg: img/diagram.svg
	$(M4) $(VARS_STEP5) $< > $@
img/build/diagram_6.svg: img/diagram.svg
	$(M4) $(VARS_STEP6) $< > $@
img/build/diagram_7.svg: img/diagram.svg
	$(M4) $(VARS_STEP7) $< > $@

img/diagram_%.png: img/build/diagram_%.svg
	$(INKSCAPE) $< -D -e $@
