"""
Classes for Django Template Linting.
"""
import re
from xsslint.utils import Expression, StringLines
from xsslint.reporting import ExpressionRuleViolation


class TransExpression(Expression):
    """
        The expression handling trans tag
    """

    def __init__(self, ruleset, results, *args, **kwargs):
        super(TransExpression, self).__init__(*args, **kwargs)
        self.string_lines = StringLines(kwargs['template'])
        self.ruleset = ruleset
        self.results = results

    def validate_expression(self, template_file, expressions=None):
        """
        Validates trans tag expression for missing escaping filter

        Arguments:
            template_file: The content of the Django template.
            results: Violations to be generated.

        Returns:
            None
        """
        trans_expr = self.expression_inner
        trans_expr_lineno = self.string_lines.index_to_line_number(self.start_index)

        # extracting translation string message
        quote = re.search(r"""\s*['"].*['"]\s*""", trans_expr, re.I)
        if not quote:
            _add_violations(self.results,
                            self.ruleset.django_trans_escape_filter_parse_error,
                            self)
            return

        pos = trans_expr.find('as', quote.end())
        if pos == -1:
            _add_violations(self.results, self.ruleset.django_trans_missing_escape, self)
            return

        trans_var_name_used = trans_expr[pos + len('as'):].strip()
        trans_expr_msg = trans_expr[quote.start():quote.end()].strip()

        if _check_is_string_has_html(trans_expr_msg):
            _add_violations(self.results,
                            self.ruleset.django_html_interpolation_missing,
                            self)
            return

        # Checking if trans tag has interpolated variables eg {}
        # in translations string. Would be tested for
        # possible html interpolation done somewhere else.
        if _check_is_string_has_variables(trans_expr_msg):
            # check for interpolate_html expression for the variable in trans expression
            interpolate_tag, html_interpolated = _is_html_interpolated(trans_var_name_used,
                                                                       expressions)

            if not html_interpolated:
                _add_violations(self.results, self.ruleset.django_html_interpolation_missing, self)
            if interpolate_tag:
                interpolate_tag.validate_expression(template_file, expressions)
            return
        escape_expr_start_pos = template_file.find('{{', self.end_index)
        if escape_expr_start_pos == -1:
            _add_violations(self.results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        # {{ found but should be on the same line as trans tag
        trans_expr_filter_lineno = self.string_lines.index_to_line_number(escape_expr_start_pos)
        if trans_expr_filter_lineno != trans_expr_lineno:
            _add_violations(self.results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        escape_expr_end_pos = template_file.find('}}', escape_expr_start_pos)
        # couldn't find matching }}
        if escape_expr_end_pos == -1:
            _add_violations(self.results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        # }} should be also on the same line
        trans_expr_filter_lineno = self.string_lines.index_to_line_number(escape_expr_end_pos)
        if trans_expr_filter_lineno != trans_expr_lineno:
            _add_violations(self.results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        escape_expr = template_file[escape_expr_start_pos + len('{{'):escape_expr_end_pos].strip(' ')
        # check escape expression has the right variable and its escaped properly
        # with force_escape filter
        if '|' not in escape_expr \
            or len(escape_expr.split('|')) != 2:
            _add_violations(self.results,
                            self.ruleset.django_trans_invalid_escape_filter,
                            self)
            return

        escape_expr_var_used, escape_filter = escape_expr.split('|')[0].strip(' '),\
                                              escape_expr.split('|')[1].strip(' ')
        if trans_var_name_used != escape_expr_var_used:
            _add_violations(self.results,
                            self.ruleset.django_escape_variable_mismatch,
                            self)
            return

        if escape_filter != 'force_escape':
            _add_violations(self.results,
                            self.ruleset.django_trans_invalid_escape_filter,
                            self)
            return

        return True

class BlockTransExpression(Expression):
    """
        The expression handling blocktrans tag
    """
    def __init__(self, ruleset, results, *args, **kwargs):
        super(BlockTransExpression, self).__init__(*args, **kwargs)
        self.string_lines = StringLines(kwargs['template'])
        self.ruleset = ruleset
        self.results = results

    def validate_expression(self, template_file, expressions=None):
        """
        Validates blocktrans tag expression for missing escaping filter

        Arguments:
            template_file: The content of the Django template.
            results: Violations to be generated.

        Returns:
            None
        """

        if not self._process_block(template_file):
            return

        filter_start_pos = template_file.rfind('{%', 0, self.start_index)
        if filter_start_pos == -1:
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_missing_escape_filter,
                            self)
            return

        filter_end_pos = template_file.find('%}', filter_start_pos)
        if filter_end_pos > self.start_index:
            _add_violations(self.results,
                            self.ruleset.django_trans_escape_filter_parse_error,
                            self)
            return

        escape_filter = template_file[filter_start_pos:filter_end_pos + 2]

        if len(escape_filter) < len('{%filter force_escape%}'):
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_missing_escape_filter,
                            self)
            return

        escape_filter = escape_filter[2:-2].strip()
        escape_filter = escape_filter.split(' ')

        if len(escape_filter) != 2:
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_missing_escape_filter,
                            self)
            return

        if escape_filter[0] != 'filter' or escape_filter[1] != 'force_escape':
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_missing_escape_filter,
                            self)
            return

        return True

    def _process_block(self, template_file):
        """
            process blocktrans..endblocktrans block

            Arguments:
                template_file: The content of the Django template.

            Returns:
                None
        """

        blocktrans_string = self._extract_translation_msg(template_file)

        # if no string extracted might have hit a parse error just return
        if not blocktrans_string:
            return

        if _check_is_string_has_html(blocktrans_string):
            _add_violations(self.results, self.ruleset.django_html_interpolation_missing, self)
            return

        return True

    def _extract_translation_msg(self, template_file):

        # Double checking parsing issues. This would have been raised by
        # Django parser. In normal case we would have a closing
        # endblocktrans for a opening blocktrans

        endblocktrans_spos = template_file.find('{%', self.end_index)
        if endblocktrans_spos == -1:
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_parse_error,
                            self)
            return
        endblocktrans_epos = template_file.find('%}', endblocktrans_spos)
        if endblocktrans_epos == -1:
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_parse_error,
                            self)
            return

        endblocktrans_tag = template_file[endblocktrans_spos:endblocktrans_epos + 2]

        # this case would not happen as the dtl parser would have already picked this up.
        if len(endblocktrans_tag) < len('{%endblocktrans%}'):
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_parse_error,
                            self)
            return

        endblocktrans_tag = endblocktrans_tag[2:-2].strip()
        if endblocktrans_tag != 'endblocktrans':
            _add_violations(self.results,
                            self.ruleset.django_blocktrans_parse_error,
                            self)
            return

        return template_file[self.end_index + 2: endblocktrans_spos].strip(' ')

class HtmlInterpolateExpression(Expression):
    """
        The expression handling interplate_html tag
    """
    def __init__(self, ruleset, results, *args, **kwargs):
        super(HtmlInterpolateExpression, self).__init__(*args, **kwargs)
        self.string_lines = StringLines(kwargs['template'])
        self.ruleset = ruleset
        self.results = results
        self.validated = False
        self.interpolated_string_var = None

        trans_expr = self.expression_inner
        # extracting interpolated variable string name
        expr_list = trans_expr.split(' ')
        if len(expr_list) < 2:
            _add_violations(self.results,
                            self.ruleset.django_html_interpolation_invalid_tag,
                            self)
            return
        self.interpolated_string_var = expr_list[1]

    def validate_expression(self, template_file, expressions=None):
        """
        Validates interpolate_html tag expression for missing safe filter for html tags

        Arguments:
            template_file: The content of the Django template.
            results: Violations to be generated.

        Returns:
            None
        """

        # if the expression is already validated, we would not be reprocessing it again
        if not self.interpolated_string_var or self.validated:
            return

        self.validated = True
        trans_expr = self.expression_inner

        html_tags = re.finditer(r"""\s*['"]</?[a-zA-Z0-9 =\-'_"]+\s*>['"]\s*""",
                                trans_expr, re.I)

        for html_tag in html_tags:
            tag_end = html_tag.end()
            escape_filter = trans_expr[tag_end:tag_end + len('|safe')]
            if escape_filter != '|safe':
                _add_violations(self.results,
                                self.ruleset.django_html_interpolation_missing_safe_filter,
                                self)
                return

        return True

def _check_is_string_has_html(trans_expr):
    html_tags = re.search(r"""</?[a-zA-Z0-9 =\-'_":]+>""", trans_expr, re.I)

    if html_tags:
        return True

def _check_is_string_has_variables(trans_expr):
    var_tags = re.search(r"""(?<!{){(?!{)[a-zA-Z0-9 =\-'_":]+(?<!})}(?!})""", trans_expr, re.I)

    if var_tags:
        return True

def _is_html_interpolated(trans_var_name_used, expressions):
    html_interpolated = False
    interpolate_tag_expr = None
    for expr in expressions:
        if isinstance(expr, HtmlInterpolateExpression):
            if expr.interpolated_string_var == trans_var_name_used:
                html_interpolated = True
                interpolate_tag_expr = expr

    return interpolate_tag_expr, html_interpolated

def _add_violations(results, rule_violation, self):
    results.violations.append(ExpressionRuleViolation(
        rule_violation, self
    ))
