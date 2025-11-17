// Flag-based language selector — single clean implementation
(function(){
    const LANGS = {
        en: { name: 'English', code: 'en', flag: '<svg width="24" height="18" viewBox="0 0 24 18" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="18" fill="#B22234"/><rect y="2" width="24" height="2" fill="#FFFFFF"/><rect y="6" width="24" height="2" fill="#FFFFFF"/><rect y="10" width="24" height="2" fill="#FFFFFF"/><rect y="14" width="24" height="2" fill="#FFFFFF"/><rect x="0" y="0" width="10" height="10" fill="#3C3B6E"/></svg>' },
        cs: { name: 'Čeština', code: 'cs', flag: '<svg width="24" height="18" viewBox="0 0 24 18" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="9" fill="#FFFFFF"/><rect y="9" width="24" height="9" fill="#D52B1E"/><rect width="24" height="6" fill="#11457E"/></svg>' }
    };

    class LangSelector {
        constructor(el){
            this.el = el;
            this.current = 'en';
            this.container = null;
            this.dropdown = null;
            this.isOpen = false;
            this.init();
        }

        async init(){
            try{
                if (window.DigiDigPreferences && window.DigiDigPreferences._initPromise) await window.DigiDigPreferences._initPromise;
            }catch(e){}

            try{
                if (window.DigiDigPreferences && window.DigiDigPreferences.getPreference){
                    const p = await window.DigiDigPreferences.getPreference('language');
                    if (p) this.current = p;
                }
            }catch(e){}

            this.render();
        }

        render(){
            this.container = document.createElement('div');
            this.container.className = 'language-selector-flags';

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'language-selector-button-flags';
            btn.innerHTML = '<div class="flag-container">'+LANGS[this.current].flag+'</div><span class="language-code">'+this.current.toUpperCase()+'</span>';
            btn.addEventListener('click', (e)=>{ e.stopPropagation(); this.toggle(); });

            this.dropdown = document.createElement('div');
            this.dropdown.className = 'language-dropdown-flags';

            Object.keys(LANGS).forEach(code => {
                const opt = document.createElement('div');
                opt.className = 'language-option-flags' + (code===this.current ? ' active' : '');
                opt.dataset.lang = code;
                opt.innerHTML = '<div class="option-flag">'+LANGS[code].flag+'</div><div class="option-content"><div class="option-name">'+LANGS[code].name+'</div></div>'+(code===this.current?'<div class="selected-indicator">✓</div>':'');
                opt.addEventListener('click', ()=> this.select(code));
                this.dropdown.appendChild(opt);
            });

            this.container.appendChild(btn);
            this.container.appendChild(this.dropdown);

            document.addEventListener('click', ()=> this.close());

            this.el.appendChild(this.container);
        }

        toggle(){ this.isOpen = !this.isOpen; this.dropdown.classList.toggle('open', this.isOpen); }
        close(){ this.isOpen = false; if (this.dropdown) this.dropdown.classList.remove('open'); }

        async select(code){
            if (code === this.current){ this.close(); return; }
            this.current = code;
            try{ if (window.DigiDigPreferences && window.DigiDigPreferences.setPreference) await window.DigiDigPreferences.setPreference('language', code); }catch(e){}
            try{ const form = new FormData(); form.append('lang', code); await fetch('/api/language', { method: 'POST', body: form }); }catch(e){}
            window.location.reload();
        }
    }

    document.addEventListener('DOMContentLoaded', ()=>{
        document.querySelectorAll('[data-component="language-selector"]').forEach(el=>{
            try{ new LangSelector(el); }catch(e){ console.error('language-selector init', e); }
        });
    });
})();
