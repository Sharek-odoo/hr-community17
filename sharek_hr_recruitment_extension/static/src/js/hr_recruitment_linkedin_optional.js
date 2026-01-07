/** @odoo-module **/


import publicWidget from "@web/legacy/js/public/public_widget";  // ✅ correct import

publicWidget.registry.hrRecruitment.include({
    _onClickApplyButton(ev) {

        const $linkedin_profile = $('#recruitment4');
        const $resume = $('#recruitment6');

        const is_resume_empty = !$resume.length || !$resume[0].files.length;

        // Resume required only if it's empty
        if (is_resume_empty) {
            $resume.attr('required', true);
        } else {
            $resume.attr('required', false);
        }

        // Always make LinkedIn optional
        $linkedin_profile.attr('required', false);
    }
});