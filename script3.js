function toggleMenu() {
    const mobileMenu = document.getElementById("mobile-menu");
    const menuIcon = document.querySelector(".menu-icon img");
  
    if (mobileMenu.style.display === "flex") {
      mobileMenu.style.display = "none";
      menuIcon.src = "./assets/images/icon-menu.svg";
    } else {
      mobileMenu.style.display = "flex";
      menuIcon.src = "./assets/images/icon-menu-close.svg";
    }
  }