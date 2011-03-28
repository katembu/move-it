/* 
 * Luhn 30 Checksum Validation
 */

var Checksum = {
    base_chars : '0123456789acdefghjklmnprtuvwxy',
    invalid : '#', /* Won't match any check digit */
    get_check_digit : function(ident) {
        var mod = this.base_chars.length;
        var factor = 1;
        var sum = 0;

        var code_point;
        var addend;
        var chr;
        for(ind in ident) {
            chr = ident[ind]; 
            code_point = this.base_chars.indexOf(chr);
            if(code_point < 0) return this.invalid;
            
            addend = factor * code_point;
            /* Alternate value of factor between 1 and 2 */
            factor == 2 ? factor = 1 : factor = 2;

            addend = Math.floor(addend / mod) + (addend % mod);
            sum += addend;
        }
        var remainder = sum % mod;
        var check_code_point = (mod - remainder) % mod;
        var out = this.base_chars[check_code_point];
        return out;
    },
    clean_chars : function(input) {
        return input.toLowerCase().replace(/\s/g,'');
    },
    is_valid_identifier : function(input) {
        var identifier = this.clean_chars(input);

        if(identifier.length < 2) return false;
        
        var check_digit = this.last_char(identifier);
        var real_chars = identifier.substr(0, identifier.length-1);

        return (this.get_check_digit(real_chars) == check_digit);
    },
    last_char : function(instr) {
        return instr[instr.length-1];
    }
}
