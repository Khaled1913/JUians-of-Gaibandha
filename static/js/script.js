/* ============================================================
   SCRIPT.JS
   JUians of Gaibandha
   Main Frontend JavaScript
============================================================ */


/* ============================================================
   DOM READY
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =====================================================
           ELEMENTS
        ===================================================== */

        const navbar =
            document.querySelector(
                ".navbar"
            );


        const menuToggle =
            document.getElementById(
                "menu-toggle"
            );


        const navMenu =
            document.getElementById(
                "nav-menu"
            );


        const navActions =
            document.getElementById(
                "nav-actions"
            );


        const navContainer =
            document.querySelector(
                ".nav-container"
            );


        const navLinks =
            document.querySelectorAll(
                ".nav-menu a"
            );


        const scrollTopButton =
            document.getElementById(
                "scrollTopBtn"
            );



        /* =====================================================
           MOBILE MENU STATE
        ===================================================== */

        function isMobileMenuOpen() {

            if (!menuToggle) {
                return false;
            }


            return (
                menuToggle.getAttribute(
                    "aria-expanded"
                )
                ===
                "true"
            );

        }



        /* =====================================================
           OPEN MOBILE MENU
        ===================================================== */

        function openMobileMenu() {

            if (
                !menuToggle
                ||
                !navMenu
            ) {
                return;
            }


            navMenu.classList.add(
                "active"
            );


            if (navActions) {

                navActions.classList.add(
                    "active"
                );

            }


            menuToggle.setAttribute(
                "aria-expanded",
                "true"
            );


            const icon =
                menuToggle.querySelector(
                    "i"
                );


            if (icon) {

                icon.classList.remove(
                    "fa-bars"
                );


                icon.classList.add(
                    "fa-xmark"
                );

            }

        }



        /* =====================================================
           CLOSE MOBILE MENU
        ===================================================== */

        function closeMobileMenu() {

            if (
                !menuToggle
                ||
                !navMenu
            ) {
                return;
            }


            navMenu.classList.remove(
                "active"
            );


            if (navActions) {

                navActions.classList.remove(
                    "active"
                );

            }


            menuToggle.setAttribute(
                "aria-expanded",
                "false"
            );


            const icon =
                menuToggle.querySelector(
                    "i"
                );


            if (icon) {

                icon.classList.remove(
                    "fa-xmark"
                );


                icon.classList.add(
                    "fa-bars"
                );

            }

        }



        /* =====================================================
           TOGGLE MOBILE MENU
        ===================================================== */

        function toggleMobileMenu() {

            if (
                isMobileMenuOpen()
            ) {

                closeMobileMenu();

            }

            else {

                openMobileMenu();

            }

        }



        /* =====================================================
           MOBILE MENU BUTTON
        ===================================================== */

        if (menuToggle) {

            menuToggle.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();

                    toggleMobileMenu();

                }
            );

        }



        /* =====================================================
           CLOSE MENU AFTER NAVIGATION
        ===================================================== */

        navLinks.forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function () {

                        if (
                            window.innerWidth
                            <=
                            992
                        ) {

                            closeMobileMenu();

                        }

                    }
                );

            }
        );



        /* =====================================================
           CLOSE MENU WHEN LOGIN BUTTON IS CLICKED
        ===================================================== */

        if (navActions) {

            const actionLinks =
                navActions.querySelectorAll(
                    "a"
                );


            actionLinks.forEach(
                function (link) {

                    link.addEventListener(
                        "click",
                        function () {

                            if (
                                window.innerWidth
                                <=
                                992
                            ) {

                                closeMobileMenu();

                            }

                        }
                    );

                }
            );

        }



        /* =====================================================
           CLOSE MENU ON OUTSIDE CLICK
        ===================================================== */

        document.addEventListener(
            "click",
            function (event) {

                if (
                    !navContainer
                    ||
                    !isMobileMenuOpen()
                ) {
                    return;
                }


                if (
                    !navContainer.contains(
                        event.target
                    )
                ) {

                    closeMobileMenu();

                }

            }
        );



        /* =====================================================
           ESCAPE KEY CLOSE
        ===================================================== */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key
                    ===
                    "Escape"
                    &&
                    isMobileMenuOpen()
                ) {

                    closeMobileMenu();


                    if (menuToggle) {

                        menuToggle.focus();

                    }

                }

            }
        );



        /* =====================================================
           WINDOW RESIZE RESET
        ===================================================== */

        let resizeTimer;


        window.addEventListener(
            "resize",
            function () {

                clearTimeout(
                    resizeTimer
                );


                resizeTimer = setTimeout(
                    function () {

                        if (
                            window.innerWidth
                            >
                            992
                        ) {

                            closeMobileMenu();

                        }

                    },
                    120
                );

            }
        );



        /* =====================================================
           NAVBAR SCROLL EFFECT
        ===================================================== */

        function updateNavbarScrollState() {

            if (!navbar) {
                return;
            }


            if (
                window.scrollY
                >
                15
            ) {

                navbar.classList.add(
                    "scrolled"
                );

            }

            else {

                navbar.classList.remove(
                    "scrolled"
                );

            }

        }


        updateNavbarScrollState();


        window.addEventListener(
            "scroll",
            updateNavbarScrollState,
            {
                passive: true
            }
        );



        /* =====================================================
           SMOOTH INTERNAL SECTION SCROLL
        ===================================================== */

        const internalLinks =
            document.querySelectorAll(
                'a[href*="#"]'
            );


        internalLinks.forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function (event) {

                        const href =
                            link.getAttribute(
                                "href"
                            );


                        if (
                            !href
                            ||
                            href === "#"
                        ) {
                            return;
                        }


                        let targetId;


                        try {

                            const url =
                                new URL(
                                    href,
                                    window.location.href
                                );


                            if (
                                url.pathname
                                !==
                                window.location.pathname
                            ) {
                                return;
                            }


                            targetId =
                                url.hash;

                        }

                        catch (error) {

                            return;

                        }


                        if (!targetId) {
                            return;
                        }


                        const target =
                            document.querySelector(
                                targetId
                            );


                        if (!target) {
                            return;
                        }


                        event.preventDefault();


                        const navbarHeight =
                            navbar
                                ?
                                navbar.offsetHeight
                                :
                                0;


                        const targetPosition =
                            target.getBoundingClientRect().top
                            +
                            window.pageYOffset
                            -
                            navbarHeight
                            -
                            12;


                        window.scrollTo(
                            {
                                top: targetPosition,
                                behavior: "smooth"
                            }
                        );


                        closeMobileMenu();

                    }
                );

            }
        );



        /* =====================================================
           SCROLL TO TOP BUTTON
        ===================================================== */

        function updateScrollTopButton() {

            if (!scrollTopButton) {
                return;
            }


            if (
                window.scrollY
                >
                450
            ) {

                scrollTopButton.classList.add(
                    "show"
                );

            }

            else {

                scrollTopButton.classList.remove(
                    "show"
                );

            }

        }


        if (scrollTopButton) {

            updateScrollTopButton();


            window.addEventListener(
                "scroll",
                updateScrollTopButton,
                {
                    passive: true
                }
            );


            scrollTopButton.addEventListener(
                "click",
                function () {

                    window.scrollTo(
                        {
                            top: 0,
                            behavior: "smooth"
                        }
                    );

                }
            );

        }



        /* =====================================================
           ACTIVE NAV LINK
           BASED ON CURRENT PAGE
        ===================================================== */

        const currentPath =
            window.location.pathname;


        navLinks.forEach(
            function (link) {

                const href =
                    link.getAttribute(
                        "href"
                    );


                if (!href) {
                    return;
                }


                try {

                    const linkUrl =
                        new URL(
                            href,
                            window.location.origin
                        );


                    if (
                        linkUrl.pathname
                        ===
                        currentPath
                        &&
                        !linkUrl.hash
                    ) {

                        link.classList.add(
                            "active"
                        );

                    }

                }

                catch (error) {

                    return;

                }

            }
        );



        /* =====================================================
           IMAGE SAFETY
        ===================================================== */

        const images =
            document.querySelectorAll(
                "img"
            );


        images.forEach(
            function (image) {

                image.addEventListener(
                    "dragstart",
                    function (event) {

                        if (
                            image.closest(
                                ".logo"
                            )
                        ) {

                            event.preventDefault();

                        }

                    }
                );

            }
        );


    }
);


/* ============================================================
   END OF FILE
============================================================ */
